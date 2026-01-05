// gerar-imagens-imagekit.js
const fs = require("fs");
const ImageKit = require("imagekit");

const imagekit = new ImageKit({
    publicKey: "public_s0hKDHUidDdV2pKFoHtf9gT9QTQ=",
    privateKey: "private_HQ6XbEc90TO8EGAkW+cuyGAPCq0=",
    urlEndpoint: "https://ik.imagekit.io/t7590uzhp/"
});

const arquivoJson = "imagens.json";
let todasImagens = [];

// 🔄 Carregar imagens existentes
if (fs.existsSync(arquivoJson)) {
    todasImagens = JSON.parse(fs.readFileSync(arquivoJson));
    console.log(`🔄 ${todasImagens.length} imagens carregadas do JSON existente.`);
}

// 🚩 Gera o nome limpo para busca eficiente
function gerarNomeLimpo(nome) {
    return nome.toLowerCase().replace(/[\.\s\-\_]/g, ""); // remove . _ espaço e caracteres especiais
}

// ✅ Verifica se já existe no JSON
function imagemExiste(nome) {
    const nomeLimpo = gerarNomeLimpo(nome);
    return todasImagens.some(img => img.nome_limpo === nomeLimpo);
}

// 🔥 Busca recursiva das imagens no ImageKit
async function buscarTodas(skip = 0) {
    console.log(`🔍 Buscando arquivos a partir de ${skip}...`);

    try {
        const arquivos = await imagekit.listFiles({
            limit: 1000,
            skip: skip
        });

        if (arquivos.length > 0) {
            const imagensConvertidas = arquivos.map(arq => {
                const nomeCompleto = arq.name.toLowerCase().trim();

                const indiceUltimoUnderscore = nomeCompleto.lastIndexOf("_");
                const nomeBase = indiceUltimoUnderscore !== -1
                    ? nomeCompleto.substring(0, indiceUltimoUnderscore).replace(/\./g, "").replace(/\s/g, "")
                    : nomeCompleto.replace(/\./g, "").replace(/\s/g, "");

                const nomeLimpo = gerarNomeLimpo(nomeBase);

                return {
                    nome: nomeBase,
                    nome_limpo: nomeLimpo,
                    url: arq.url
                };
            });

            const novasImagens = imagensConvertidas.filter(img => !imagemExiste(img.nome));

            if (novasImagens.length > 0) {
                todasImagens.push(...novasImagens);
                fs.writeFileSync(arquivoJson, JSON.stringify(todasImagens, null, 2));
                console.log(`✅ ${novasImagens.length} novas imagens adicionadas. Total agora: ${todasImagens.length}`);
            } else {
                console.log("ℹ️ Nenhuma nova imagem encontrada nesta rodada.");
            }

            await buscarTodas(skip + arquivos.length);
        } else {
            console.log("🏁 Fim da busca. Nenhum arquivo restante.");
        }
    } catch (err) {
        console.error("❌ Erro ao buscar arquivos:", err.message);
        console.log("⏳ Tentando novamente em 5 segundos...");
        await new Promise(res => setTimeout(res, 5000));
        await buscarTodas(skip);
    }
}

// 🚀 Inicia a busca
buscarTodas();