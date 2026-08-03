const fs = require("fs");
const path = require("path");
const sharp = require("sharp");

const inputDir = path.resolve(__dirname, "../assets/product-plan-v2");
const files = fs.readdirSync(inputDir).filter((name) => name.endsWith(".svg"));

async function main() {
  for (const file of files) {
    const source = path.join(inputDir, file);
    const target = path.join(inputDir, file.replace(/\.svg$/, ".png"));
    await sharp(source, { density: 144 }).png().toFile(target);
  }
  process.stdout.write(`rendered ${files.length} PNG files\n`);
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exitCode = 1;
});
