// gerarImagensJson.js
const fs = require("fs");
const path = require("path");

const pastaImagens = "./imagens";
const arquivos = fs.readdirSync(pastaImagens);

const imagens = arquivos.filter(nome => /\.(jpe?g|png|webp)$/i.test(nome));

fs.writeFileSync("imagens.json", JSON.stringify(imagens, null, 2));
console.log("✅ imagens.json gerado com sucesso!");
