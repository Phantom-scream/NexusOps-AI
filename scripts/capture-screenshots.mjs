#!/usr/bin/env node

import fs from "node:fs/promises";

const [, , token, email, outputDir = "docs/screenshots"] = process.argv;

if (!token || !email) {
  console.error("Usage: node scripts/capture-screenshots.mjs <access-token> <email> [output-dir]");
  process.exit(1);
}

const chromeEndpoint = "http://127.0.0.1:9222";
const pages = [
  ["dashboard", "http://localhost:3000/dashboard"],
  ["infrastructure", "http://localhost:3000/clusters"],
  ["incidents", "http://localhost:3000/incidents"],
  ["security", "http://localhost:3000/security"],
  ["cost-optimization", "http://localhost:3000/cost"],
  ["ai-investigation", "http://localhost:3000/ai"],
];

const targetResponse = await fetch(`${chromeEndpoint}/json/new?about:blank`, { method: "PUT" });
if (!targetResponse.ok) {
  throw new Error(`Unable to create Chrome target: ${targetResponse.status}`);
}

const target = await targetResponse.json();
const socket = new WebSocket(target.webSocketDebuggerUrl);
let nextId = 1;
const pending = new Map();
const events = [];

socket.onmessage = (message) => {
  const payload = JSON.parse(message.data);
  if (payload.id && pending.has(payload.id)) {
    const { resolve, reject } = pending.get(payload.id);
    pending.delete(payload.id);
    if (payload.error) {
      reject(new Error(JSON.stringify(payload.error)));
    } else {
      resolve(payload.result || {});
    }
    return;
  }
  if (payload.method) {
    events.push(payload);
  }
};

await new Promise((resolve) => {
  socket.onopen = resolve;
});

function send(method, params = {}) {
  const id = nextId;
  nextId += 1;
  socket.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
  });
}

function wait(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

async function navigate(url) {
  events.length = 0;
  await send("Page.navigate", { url });
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (events.some((event) => event.method === "Page.loadEventFired")) {
      return;
    }
    await wait(100);
  }
}

await fs.mkdir(outputDir, { recursive: true });
await send("Page.enable");
await send("Runtime.enable");
await send("Emulation.setDeviceMetricsOverride", {
  width: 1440,
  height: 1100,
  deviceScaleFactor: 1,
  mobile: false,
});

await navigate("http://localhost:3000/login");
await send("Runtime.evaluate", {
  expression: `localStorage.setItem('nexusops-auth', ${JSON.stringify(
    JSON.stringify({
      state: { token, refreshToken: token, email, role: "viewer" },
      version: 0,
    }),
  )})`,
});

const saved = [];
for (const [name, url] of pages) {
  await navigate(url);
  await wait(3500);
  const screenshot = await send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
  });
  const filePath = `${outputDir}/${name}.png`;
  await fs.writeFile(filePath, Buffer.from(screenshot.data, "base64"));
  saved.push(filePath);
}

socket.close();
console.log(saved.join("\n"));
