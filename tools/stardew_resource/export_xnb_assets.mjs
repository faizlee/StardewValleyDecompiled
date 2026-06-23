#!/usr/bin/env node

import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const defaultFarmOldRoot = path.resolve(scriptDir, "..", "..");

function parseArgs(argv) {
  const args = {
    farmoldRoot: defaultFarmOldRoot,
    input: "",
    output: "",
    xnbModule: "",
  };

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === "--farmold-root") {
      args.farmoldRoot = next;
      i += 1;
    } else if (arg === "--input") {
      args.input = next;
      i += 1;
    } else if (arg === "--output") {
      args.output = next;
      i += 1;
    } else if (arg === "--xnb-module") {
      args.xnbModule = next;
      i += 1;
    } else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!args.input || !args.output) {
    printHelp();
    throw new Error("--input and --output are required");
  }

  args.farmoldRoot = path.resolve(args.farmoldRoot);
  args.input = path.resolve(args.input);
  args.output = path.resolve(args.output);
  if (!args.xnbModule) {
    args.xnbModule = path.join(
      args.farmoldRoot,
      "_local_exports",
      "xnb_js_tool",
      "node_modules",
      "xnb",
      "dist",
      "xnb.module.js",
    );
  }
  args.xnbModule = path.resolve(args.xnbModule);
  return args;
}

function printHelp() {
  console.log(`Usage:
node tools/stardew_resource/export_xnb_assets.mjs --input <items.json> --output <output-root> [--farmold-root <path>]

The input JSON must be either an array or an object with an "items" array.
Each item requires:
  content_path, category, source_type, source_path, output_group
`);
}

function csvEscape(value) {
  const text = value === undefined || value === null ? "" : String(value);
  if (/[",\r\n]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

function toPosix(value) {
  return String(value ?? "").replaceAll("\\", "/");
}

function stripKnownExtension(value) {
  return value.replace(/\.(xnb|fnt|json)$/i, "");
}

async function writeCsv(filePath, headers, rows) {
  const lines = [headers.map(csvEscape).join(",")];
  for (const row of rows) {
    lines.push(headers.map((header) => csvEscape(row[header])).join(","));
  }
  await writeFile(filePath, `${lines.join("\n")}\n`, "utf8");
}

async function blobToBuffer(data) {
  if (data instanceof Blob) {
    return Buffer.from(await data.arrayBuffer());
  }
  return Buffer.from(data);
}

async function decodeItem(XNB, outputRoot, item) {
  const sourcePath = path.resolve(item.source_path);
  const contentPath = toPosix(item.content_path);
  const outputGroup = toPosix(item.output_group || "decoded");
  const relativeNoExt = stripKnownExtension(contentPath);
  const baseFileName = path.basename(contentPath);
  const buffer = await readFile(sourcePath);

  const originalLog = console.log;
  const originalWarn = console.warn;
  console.log = () => {};
  console.warn = () => {};
  let outputs;
  try {
    outputs = await XNB.unpackToFiles(buffer, {
      fileName: baseFileName,
      contentOnly: true,
    });
  } finally {
    console.log = originalLog;
    console.warn = originalWarn;
  }

  const records = [];
  for (const output of outputs) {
    const bytes = await blobToBuffer(output.data);
    const extension = String(output.extension || "bin").replace(/^\./, "");
    const relativeOutput = toPosix(path.posix.join(outputGroup, `${relativeNoExt}.${extension}`));
    const outputPath = path.join(outputRoot, ...relativeOutput.split("/"));
    await mkdir(path.dirname(outputPath), { recursive: true });
    await writeFile(outputPath, bytes);
    records.push({
      content_path: contentPath,
      category: item.category || "",
      source_type: item.source_type || "",
      source_path: sourcePath,
      output_relative_path: relativeOutput,
      extension,
      bytes: bytes.length,
      status: "decoded",
      decoder: "xnb-js",
    });
  }

  return records;
}

async function main() {
  const args = parseArgs(process.argv);
  await mkdir(args.output, { recursive: true });

  const XNB = await import(pathToFileURL(args.xnbModule).href);
  const inputJson = JSON.parse(await readFile(args.input, "utf8"));
  const items = Array.isArray(inputJson) ? inputJson : inputJson.items;
  if (!Array.isArray(items)) {
    throw new Error("Input JSON must be an array or an object with an items array");
  }

  const records = [];
  const failures = [];
  for (const item of items) {
    try {
      const decoded = await decodeItem(XNB, args.output, item);
      records.push(...decoded);
    } catch (error) {
      failures.push({
        content_path: toPosix(item.content_path),
        category: item.category || "",
        source_type: item.source_type || "",
        source_path: path.resolve(item.source_path || ""),
        error_type: error?.constructor?.name || "Error",
        message: error?.message || String(error),
        status: "decode_failed",
        decoder: "xnb-js",
      });
    }
  }

  await writeCsv(
    path.join(args.output, "xnb_decode_index.csv"),
    [
      "content_path",
      "category",
      "source_type",
      "source_path",
      "output_relative_path",
      "extension",
      "bytes",
      "status",
      "decoder",
    ],
    records,
  );
  await writeCsv(
    path.join(args.output, "xnb_decode_failures.csv"),
    ["content_path", "category", "source_type", "source_path", "error_type", "message", "status", "decoder"],
    failures,
  );

  const summary = {
    schema: "farmold-stardew-xnb-decode-v1",
    generated_at_local: new Date().toISOString(),
    input: args.input,
    output_root: args.output,
    attempted_items: items.length,
    decoded_items: new Set(records.map((record) => record.content_path)).size,
    output_files: records.length,
    failed_items: failures.length,
    by_category: Object.values(
      records.reduce((acc, record) => {
        const key = record.category || "(unknown)";
        if (!acc[key]) {
          acc[key] = { category: key, output_files: 0, bytes: 0 };
        }
        acc[key].output_files += 1;
        acc[key].bytes += Number(record.bytes || 0);
        return acc;
      }, {}),
    ).sort((a, b) => a.category.localeCompare(b.category)),
  };
  await writeFile(path.join(args.output, "xnb_decode_summary.json"), `${JSON.stringify(summary, null, 2)}\n`, "utf8");
  console.log(JSON.stringify(summary, null, 2));
}

main().catch((error) => {
  console.error(error?.stack || error);
  process.exit(1);
});
