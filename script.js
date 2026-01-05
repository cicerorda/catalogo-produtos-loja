let produtos = [];
let paginaAtual = 1;
const itensPorPagina = 27;
let categoriasUnicas = new Set();
let categoriasSelecionadas = new Set();
let termoBusca = "";
let grupoAtual = 1;
const botoesPorGrupo = 10;
let totalPaginas = 0;

let listaImagens = [];
let mapaImagemPorNomeLimpo = new Map(); // 🆕 mapa rápido nome → url

const BASE_IMAGEKIT_URL = "https://ik.imagekit.io/t7590uzhp/imagens/";
const URL_SEM_IMAGEM = "https://ik.imagekit.io/t7590uzhp/imagens/sem-imagem_Ga_BH1QVQo.jpg";

// Cache de variantes e de imagem por referência
const cacheVariantes = new Map();
const cacheImagemPorRef = new Map(); // 🆕 cache ref → url

// Listas auxiliares para paginação com deduplicação por imagem
let listaFiltradaAtual = [];         // tudo filtrado
let listaFiltradaSemDuplicatas = []; // filtrado + 1 por imagem


console.log("✅ script.js foi carregado!");

function gerarVariantesComCache(ref) {
  if (cacheVariantes.has(ref)) return cacheVariantes.get(ref);
  const variantes = gerarVariantes(ref);
  cacheVariantes.set(ref, variantes);
  return variantes;
}

function limparTexto(texto) {
  return (texto || "").toLowerCase().replace(/[.\s\-_]/g, "");
}

function removerSufixoDeVariacao(ref) {
  return (ref ?? "").toString().split(/[-_]/)[0];
}

function baseDoisBlocos(ref) {
  const s = (ref ?? "").toString().toLowerCase().trim();
  const partes = s.split(".");
  if (partes.length >= 2) return `${partes[0]}.${partes[1]}`;
  return s;
}

function removerZerosEsquerdaPrimeiroBloco(refDoisBlocos) {
  const [a, b] = refDoisBlocos.split(".");
  const aSemZero = (a || "").replace(/^0+/, "") || "0";
  return `${aSemZero}.${b}`;
}

function gerarVariantes(ref) {
  const variantes = new Set();
  const crua = limparTexto(ref);
  variantes.add(crua);

  const doisBlocos = baseDoisBlocos(ref);
  variantes.add(limparTexto(doisBlocos));

  const doisBlocosSemZeros = removerZerosEsquerdaPrimeiroBloco(doisBlocos);
  variantes.add(limparTexto(doisBlocosSemZeros));

  let tmp = (ref ?? "").toString();
  while (/\.(?:0{1,3})$/.test(tmp)) {
    tmp = tmp.replace(/\.(?:0{1,3})$/, "");
    variantes.add(limparTexto(tmp));
    const db = baseDoisBlocos(tmp);
    variantes.add(limparTexto(db));
  }

  const semSufixo = limparTexto(removerSufixoDeVariacao(ref));
  variantes.add(semSufixo);

  if (semSufixo.endsWith("00") && semSufixo.length > 6) {
    variantes.add(semSufixo.slice(0, -2));
  }

  // 🔧 CASO ESPECIAL: e.20530.15 para E020530.15.000
  if (/^e0?\d{5}\.\d{2}\.000$/i.test(ref)) {
    const vMatch = ref.match(/^e0?(\d{5})\.(\d{2})\.000$/i);
    if (vMatch) {
      const vCustom = `e.${parseInt(vMatch[1], 10)}.${vMatch[2]}`;
      variantes.add(limparTexto(vCustom));
    }
  }

  // 🔧 CASO: E18440.07.00 → gerar E18440.00 (mesmo padrão da imagem e1844000)
    const m2 = ref.match(/^E(\d{5})\.(\d{2})\.(\d{2})$/i);
    if (m2) {
      const bloco1 = m2[1]; // 18440
      const bloco2 = m2[3]; // 00

      // E18440.00
      const refSemBlocoIntermediario = `E${bloco1}.${bloco2}`;
      variantes.add(limparTexto(refSemBlocoIntermediario)); // e1844000
      variantes.add(refSemBlocoIntermediario.toLowerCase());
      variantes.add(`e${bloco1}${bloco2}`);
    }

  // 🔧 NOVO CASO: tratar E0xxxxx.xx → gerar variantes sem o zero depois do E
  const m = ref.match(/^E0(\d{5})\.(\d{2})/i);
  if (m) {
    const bloco1 = m[1]; // ex: 23241
    const bloco2 = m[2]; // ex: 27

    variantes.add(`e${bloco1}${bloco2}`);
    variantes.add(limparTexto(`e.${bloco1}.${bloco2}`));
    variantes.add(`e.${bloco1}.${bloco2}`);
  }

  return Array.from(variantes);
}

function encontrarImagem(ref) {
  if (!ref) return URL_SEM_IMAGEM;

  // Cache: mesma referência → mesma URL
  if (cacheImagemPorRef.has(ref)) {
    return cacheImagemPorRef.get(ref);
  }

  const variantes = gerarVariantesComCache(ref);
  let urlEncontrada = URL_SEM_IMAGEM;

  for (const v of variantes) {
    const url = mapaImagemPorNomeLimpo.get(v); // consulta no Map
    if (url) {
      urlEncontrada = url;
      break;
    }
  }

  cacheImagemPorRef.set(ref, urlEncontrada);
  return urlEncontrada;
}

fetch("imagens.json")
  .then(res => {
    console.log("Resposta bruta imagens.json:", res);
    return res.json();
  })
  .then(data => {
    console.log("✔️ JSON de imagens carregado com sucesso:", data);
  })
  .catch(err => {
    console.error("❌ Erro ao carregar imagens.json:", err);
  });

fetch("produtos.json")
  .then(res => {
    console.log("Resposta bruta produtos.json:", res);
    return res.json();
  })
  .then(data => {
    console.log("✔️ JSON de produtos carregado com sucesso:", data);
  })
  .catch(err => {
    console.error("❌ Erro ao carregar produtos.json:", err);
  });

let imagensCarregadas = false;
let produtosCarregados = false;

fetch("imagens.json")
  .then(res => res.json())
  .then(imagensData => {
    listaImagens = imagensData.map(img => ({
      ...img,
      nome_limpo: processarNomeImagem(img.nome)
    }));

    // 🆕 monta mapa nome_limpo → url para busca O(1)
    mapaImagemPorNomeLimpo = new Map();
    listaImagens.forEach(img => {
      if (img.nome_limpo) {
        mapaImagemPorNomeLimpo.set(img.nome_limpo, img.url);
      }
    });

    console.log("🔍 Imagens carregadas:", listaImagens);
    imagensCarregadas = true;

    if (produtosCarregados) {
      atualizarProdutos();
    }
  })
  .catch(err => console.error("❌ Erro ao carregar imagens.json:", err));

fetch("produtos.json")
  .then(res => res.json())
  .then(produtosData => {
    produtos = produtosData;

    produtos.forEach(produto => {
      if (produto.Categoria) {
        const partes = produto.Categoria.split("_");
        const categoriaLimpa = partes[partes.length - 1];
        produto.CategoriaLimpa = categoriaLimpa;
        categoriasUnicas.add(categoriaLimpa);
      }
    });

    criarListaDeCategorias();
    produtosCarregados = true;

    if (imagensCarregadas) {
      atualizarProdutos();
    }
  })
  .catch(err => console.error("❌ Erro ao carregar produtos.json:", err));


function processarNomeImagem(nome) {
    const nomeOriginal = nome.toLowerCase();
    const partes = nomeOriginal.split("_");

    let nomeBase = partes[0];

    // Se for tipo ctc_005800 → mantém inteiro
    if (partes.length > 1 && /^[a-z]+$/.test(partes[0])) {
        nomeBase = partes[0] + partes[1];
    }

    const nomeLimpo = nomeBase.replace(/[\.\s\-_]/g, "");
    return nomeLimpo;
}

// 🔹 Criar lista de categorias com checkboxes invisíveis e clique no nome
function criarListaDeCategorias() {
    const listaCategorias = document.getElementById("category-list");
    listaCategorias.innerHTML = "";

    categoriasUnicas.forEach(categoria => {
        const item = document.createElement("li");

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.classList.add("categoria-checkbox");
        checkbox.value = categoria;
        checkbox.checked = categoriasSelecionadas.has(categoria);

        const label = document.createElement("label");
        label.textContent = categoria;
        label.addEventListener("click", () => {
            checkbox.checked = !checkbox.checked;
            atualizarFiltroCategorias();
        });

        item.appendChild(checkbox);
        item.appendChild(label);
        listaCategorias.appendChild(item);
    });

    // Adiciona um único evento para toda a lista de categorias
    listaCategorias.addEventListener("change", atualizarFiltroCategorias);
}

// Atualiza a lista de categorias selecionadas
function atualizarFiltroCategorias() {
    categoriasSelecionadas = new Set(
        [...document.querySelectorAll(".categoria-checkbox:checked")].map(cb => cb.value)
    );
    paginaAtual = 1;
    atualizarProdutos();
}

// 🔹 Atualiza a seleção de categorias e recarrega produtos
function toggleCategoria(categoria, selecionado) {
    selecionado ? categoriasSelecionadas.add(categoria) : categoriasSelecionadas.delete(categoria);
    paginaAtual = 1;
    atualizarProdutos();
}

function obterProdutosFiltrados() {
    return produtos
        .filter(p =>
            categoriasSelecionadas.size === 0 ||
            categoriasSelecionadas.has(p.CategoriaLimpa)
        )
        .filter(p => {
            const ref = String(p.Referencia ?? "").toLowerCase();
            const desc = String(p.Descricao ?? "").toLowerCase();
            const termo = termoBusca.toLowerCase().trim();

            if (!termo) return true;

            return ref.includes(termo) || desc.includes(termo);
        });
}

// 🔹 Atualizar produtos e paginação
function atualizarProdutos() {
  // 1) aplica filtros (categoria + busca)
  listaFiltradaAtual = obterProdutosFiltrados();

  // 2) remove duplicados por URL de imagem na lista inteira filtrada
  const urlsVistas = new Set();
  listaFiltradaSemDuplicatas = [];

  for (const produto of listaFiltradaAtual) {
    const url = encontrarImagem(produto.Referencia);

    if (!urlsVistas.has(url)) {
      urlsVistas.add(url);
      listaFiltradaSemDuplicatas.push(produto);
    }
  }

  // 3) calcula paginação em cima da lista SEM duplicatas
  totalPaginas = Math.ceil(listaFiltradaSemDuplicatas.length / itensPorPagina);
  if (paginaAtual > totalPaginas) paginaAtual = 1; // segurança
  grupoAtual = Math.ceil(paginaAtual / botoesPorGrupo);

  // 4) exibe e desenha paginação
  exibirProdutos(listaFiltradaSemDuplicatas);
  criarPaginacao(listaFiltradaSemDuplicatas);
}

// 🔹 Buscar categorias
function filtrarCategorias() {
    let termoBuscaCategoria = document.getElementById("search-category").value.toLowerCase();

    // Verifica todas as categorias existentes
    let categoriasFiltradas = [...categoriasUnicas].filter(cat => 
        cat.toLowerCase().includes(termoBuscaCategoria)
    );

    const listaCategorias = document.getElementById("category-list");
    listaCategorias.innerHTML = "";

    if (categoriasFiltradas.length === 0) {
        listaCategorias.innerHTML = `<p class="mensagem-nenhum-produto">Nenhuma categoria encontrada.</p>`;
        return;
    }

    categoriasFiltradas.forEach(cat => {
        const item = document.createElement("li");
        
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.value = cat;
        checkbox.checked = categoriasSelecionadas.has(cat);
        checkbox.addEventListener("change", () => toggleCategoria(cat, checkbox.checked));

        const label = document.createElement("label");
        label.textContent = cat;
        label.addEventListener("click", () => {
            checkbox.checked = !checkbox.checked;
            toggleCategoria(cat, checkbox.checked);
        });

        item.appendChild(checkbox);
        item.appendChild(label);
        listaCategorias.appendChild(item);
    });
}

// 🔹 Criar botões de paginação
function criarPaginacao(lista) {
    totalPaginas = Math.ceil(lista.length / itensPorPagina);
    const paginacaoContainer = document.getElementById("pagination");
    paginacaoContainer.innerHTML = "";

    const inicioGrupo = (grupoAtual - 1) * botoesPorGrupo + 1;
    const fimGrupo = Math.min(inicioGrupo + botoesPorGrupo - 1, totalPaginas);

    if (grupoAtual > 1) {
        paginacaoContainer.appendChild(criarBotao("⟨", () => mudarGrupo(grupoAtual - 1)));
    }

    for (let i = inicioGrupo; i <= fimGrupo; i++) {
        const btn = criarBotao(i, () => mudarPagina(i));
        if (i === paginaAtual) btn.classList.add("active");
        paginacaoContainer.appendChild(btn);
    }

    if (fimGrupo < totalPaginas) {
        paginacaoContainer.appendChild(criarBotao("⟩", () => mudarGrupo(grupoAtual + 1)));
    }
}

// 🔹 Criar botão reutilizável
function criarBotao(texto, funcao) {
    const btn = document.createElement("button");
    btn.textContent = texto;
    btn.classList.add("pagina-btn");
    btn.addEventListener("click", funcao);
    return btn;
}

// 🔹 Mudar grupo de páginas
function mudarGrupo(novoGrupo) {
  grupoAtual = novoGrupo;
  criarPaginacao(listaFiltradaSemDuplicatas);
}

function mudarPagina(pagina) {
  paginaAtual = pagina;
  exibirProdutos(listaFiltradaSemDuplicatas);
  criarPaginacao(listaFiltradaSemDuplicatas);
}

// 🔹 Toggle da lista de categorias
document.querySelector(".filter-header").addEventListener("click", () => {
    const filterContent = document.getElementById("category-filter");
    filterContent.classList.toggle("active");
});

let listaDeCompras = [];

// 🔹 Função para adicionar um produto à lista de compras
function adicionarAoCarrinho(referencia) {
    // Busca o produto na lista de produtos pelo código de referência
    const produto = produtos.find(p => p.Referencia === referencia);
    
    if (!produto) return;

    // Obtém a quantidade informada pelo usuário
    const quantidadeInput = document.getElementById(`quantidade-${referencia}`);
    const quantidade = parseInt(quantidadeInput.value);

    if (quantidade <= 0 || isNaN(quantidade)) {
        alert("Por favor, insira uma quantidade válida.");
        return;
    }

    // Verifica se o produto já está no carrinho
    const produtoNoCarrinho = listaDeCompras.find(item => item.Referencia === referencia);

    if (produtoNoCarrinho) {
        // Se já existir, apenas aumenta a quantidade
        produtoNoCarrinho.Quantidade += quantidade;
    } else {
        // Se não existir, adiciona ao carrinho
        listaDeCompras.push({ ...produto, Quantidade: quantidade });
    }

    atualizarCarrinho();
}

function exibirProdutos(produtos) {
  const container = document.getElementById("produtos-container");
  container.innerHTML = "";

  produtos.forEach((produto) => {
    const card = document.createElement("div");
    card.classList.add("card");

    const imagemUrl = encontrarImagem(produto.Referencia, listaImagens);
    const img = document.createElement("img");
    img.alt = produto.Referencia;

    if (imagemUrl) {
      img.src = imagemUrl;
    } else {
      img.src = "https://via.placeholder.com/150x100?text=Sem+Imagem";
      card.style.border = "2px dashed red"; // opcional: destacar cards sem imagem
    }

    const ref = document.createElement("h3");
    ref.textContent = produto.Referencia;

    const desc = document.createElement("p");
    desc.textContent = produto.Descricao;

    card.appendChild(img);
    card.appendChild(ref);
    card.appendChild(desc);
    container.appendChild(card);
  });
}

// ✅ Exibir produtos na tela (sem repetir mesma imagem na página)
function exibirProdutos(lista) {
  const container = document.getElementById("products");
  container.innerHTML = "";

  const inicio = (paginaAtual - 1) * itensPorPagina;
  const produtosPagina = lista.slice(inicio, inicio + itensPorPagina);

  if (!produtosPagina.length) {
    container.innerHTML = `<p class="mensagem-nenhum-produto">Nenhum produto encontrado.</p>`;
    return;
  }

  produtosPagina.forEach(produto => {
    const card = document.createElement("div");
    card.classList.add("card");

    const caminhoImagem = encontrarImagem(produto.Referencia);

    const precoFormatado = produto.Preco
  ? produto.Preco.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL"
    })
  : "Sob consulta";

    card.innerHTML = `
      <div class="image-container">
        <img src="${caminhoImagem}" alt="Imagem do produto"
          onerror="this.src='${URL_SEM_IMAGEM}'">
      </div>

      <div class="container">
        <h5>${produto.Referencia || "Sem Referência"}</h5>
        <p>${produto.Descricao || "Sem Descrição"}</p>

        <p class="preco">${precoFormatado}</p>

        <h6>Categoria: ${produto.Categoria || "Sem Categoria"}</h6>
      </div>
    `;

    container.appendChild(card);
  });
}


function atualizarCarrinho() {
    const cartContainer = document.getElementById("cart-items");
    cartContainer.innerHTML = "";

    if (listaDeCompras.length === 0) {
        cartContainer.innerHTML = "<p>Nenhum item na lista.</p>";
        return;
    }

    listaDeCompras.forEach((produto, index) => {
        const item = document.createElement("li");

        item.innerHTML = `
            <span>${produto.Referencia}</span>
            
            <div>
                <input type="number" min="1" value="${produto.Quantidade}" 
                    onchange="atualizarQuantidade(${index}, this.value)">
                <button onclick="removerDoCarrinho(${index})">❌</button>
            </div>
        `;
        cartContainer.appendChild(item);
    });
}

// 🔹 Atualiza a quantidade diretamente no carrinho
function atualizarQuantidade(index, novaQuantidade) {
    novaQuantidade = parseInt(novaQuantidade);

    if (novaQuantidade > 0) {
        listaDeCompras[index].Quantidade = novaQuantidade;
        atualizarCarrinho();
    } else {
        removerDoCarrinho(index); // Se a quantidade for 0, remove o item
    }
}

// 🔹 Remove um item do carrinho
function removerDoCarrinho(index) {
    listaDeCompras.splice(index, 1);
    atualizarCarrinho();
}

document.addEventListener("DOMContentLoaded", function () {
    setTimeout(() => {
        const btnDownload = document.getElementById("download-pdf");

        if (btnDownload) {
            console.log("✅ Botão 'Baixar Pesquisa' encontrado!");

            btnDownload.addEventListener("click", function () {
                console.log("🎯 Botão clicado!");
                baixarPesquisaEmPDF();
            });

        } else {
            console.error("❌ Erro: Botão 'Baixar Pesquisa' NÃO encontrado no HTML.");
        }
        // 🔽 Ativa o campo de busca principal
        function debounce(func, delay) {
            let timeout;
            return function (...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), delay);
            };
        }

        const inputBusca = document.getElementById("search-input");
        if (inputBusca) {
            inputBusca.addEventListener("input", debounce((event) => {
                termoBusca = event.target.value.trim();
                console.log("🔎 termoBusca atualizado:", termoBusca);
                paginaAtual = 1;
                atualizarProdutos();
            }, 300)); // você pode ajustar esse tempo se quiser
        }
    }, 1000); // Espera 1 segundo para garantir que o DOM foi carregado
});

// 🔹 Limpa toda a lista de compras
document.getElementById("clear-cart").addEventListener("click", () => {
    if (confirm("Tem certeza que deseja limpar a lista de compras?")) {
        listaDeCompras = [];
        atualizarCarrinho();
    }
});

function baixarPesquisaEmPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });

    // 🟡 Base para o PDF:
    // se já temos a lista sem duplicatas (tela atual), reaproveita
    // se não, cai para obterProdutosFiltrados() como fallback
    let baseLista = (Array.isArray(listaFiltradaSemDuplicatas) && listaFiltradaSemDuplicatas.length)
        ? listaFiltradaSemDuplicatas
        : obterProdutosFiltrados();

    if (!baseLista.length) {
        alert("Nenhum item encontrado.");
        return;
    }

    // 🟢 Remove duplicados por imagem também no PDF
    const urlsVistas = new Set();
    const listaSemDuplicatas = [];

    for (const produto of baseLista) {
        const urlImg = encontrarImagem(produto.Referencia);

        if (!urlsVistas.has(urlImg)) {
            urlsVistas.add(urlImg);
            listaSemDuplicatas.push(produto);
        }
    }

    if (!listaSemDuplicatas.length) {
        alert("Nenhum item encontrado.");
        return;
    }

    // 📝 Cabeçalho
    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.text("Catálogo de Produtos", 10, 15);

    let x = 10, y = 25;
    const larguraCard = 62;
    const alturaCard = 62;
    const imgMaxLargura = 50;
    const imgMaxAltura = 30;
    const espacamentoX = 3;
    const espacamentoY = 3;
    const colunas = 3;

    // 🔄 Carrega imagens de todos os produtos (sem duplicatas)
    const promessas = listaSemDuplicatas.map(produto => {
        return new Promise(resolve => {
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => resolve({ produto, img });
            img.onerror = () => resolve({ produto, img: null });
            img.src = encontrarImagem(produto.Referencia);
        });
    });

    Promise.all(promessas).then(resultados => {
        resultados.forEach(({ produto, img }, index) => {
            // Card de fundo
            doc.setFillColor(245, 245, 245);
            doc.roundedRect(x, y, larguraCard, alturaCard, 3, 3, "FD");

            // Imagem (se carregou)
            if (img) {
                const canvas = document.createElement("canvas");
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(img, 0, 0);
                const base64 = canvas.toDataURL("image/jpeg");

                const escala = Math.min(
                    imgMaxLargura / img.width,
                    imgMaxAltura / img.height
                );
                const imgLarguraAjustada = img.width * escala;
                const imgAlturaAjustada = img.height * escala;

                doc.addImage(
                    base64,
                    "JPEG",
                    x + (larguraCard - imgLarguraAjustada) / 2,
                    y + 5,
                    imgLarguraAjustada,
                    imgAlturaAjustada
                );
            }

            const textoY = y + imgMaxAltura + 12;
            doc.setFontSize(9);
            doc.setTextColor(0, 0, 0);
            doc.setFont("helvetica", "bold");
            doc.text((produto.Referencia || "Sem Referência").toString(), x + 5, textoY);

            doc.setFont("helvetica", "normal");
            const desc = doc.splitTextToSize(
                (produto.Descricao || "Sem Descrição").toString(),
                larguraCard - 10
            );
            doc.text(desc, x + 5, textoY + 5);

            doc.setFont("helvetica", "italic");
            doc.setFontSize(8);
            doc.setTextColor(100);
            doc.text(`Cat: ${(produto.CategoriaLimpa || "Sem Categoria")}`, x + 5, textoY + 15);

            // Próximo card (3 colunas)
            if ((index + 1) % colunas === 0) {
                x = 10;
                y += alturaCard + espacamentoY;
            } else {
                x += larguraCard + espacamentoX;
            }

            // Próxima página se precisar
            if (y + alturaCard > 295) {
                doc.addPage();
                y = 25;
                x = 10;
            }

            doc.setTextColor(0, 0, 0);
        });

        doc.save("catalogo_produtos.pdf");
    });
}

console.log("Verificando jsPDF:", window.jspdf);

function gerarRelatorioSemImagem() {
    const semImagem = produtos.filter(p => encontrarImagem(p.Referencia).includes("sem-imagem.jpg"));

    console.warn(`🔍 Total de produtos sem imagem: ${semImagem.length}`);
    console.table(semImagem.map(p => ({
        Referencia: p.Referencia,
        Descricao: p.Descricao,
        Categoria: p.Categoria
    })));
}

// Chamar após carregar tudo
setTimeout(() => {
    if (produtos.length > 0 && listaImagens.length > 0) {
        gerarRelatorioSemImagem();
    } else {
        console.warn("⚠️ Produtos ou imagens ainda não carregados para gerar o relatório.");
    }
}, 2000);