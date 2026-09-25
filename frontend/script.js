(function(){
  var API_URL = "http://127.0.0.1:8000/articles";
  var PAGE_SIZE = 20;
  var CATEGORIES = [
    {key:"AI", label:"AI", tag:"AI"},
    {key:"Data", label:"Data", tag:"Data"},
    {key:"Cloud", label:"Cloud", tag:"Cloud"}
  ];
  var SOURCE_LABELS = {"dev.to":"Dev.to","devto":"Dev.to","medium":"Medium","freecodecamp":"freeCodeCamp","fcc":"freeCodeCamp","pluralsight":"Pluralsight","geeksforgeeks":"GeeksforGeeks","gfg":"GeeksforGeeks"};
  var SOURCE_KEYS = {"dev.to":"devto","devto":"devto","medium":"medium","freecodecamp":"fcc","fcc":"fcc","pluralsight":"pluralsight","geeksforgeeks":"gfg","gfg":"gfg"};

  var ARTICLES = [];
  var currentArticle = null;
  var state = {view:"browse", category:"AI", query:"", loading:true, error:"", articleId:null, page:1, total:0, totalPages:1};
  var saved = new Set();
  try{ var raw=localStorage.getItem("techhub_saved"); if(raw) JSON.parse(raw).forEach(function(id){saved.add(id);}); }catch(e){}
  function persistSaved(){ try{localStorage.setItem("techhub_saved",JSON.stringify(Array.from(saved)));}catch(e){} }
  function escapeHtml(v){return String(v==null?"":v).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");}
  function normalizeAuthor(v){if(!v)return "Unknown";var t=String(v).trim(),m=t.match(/^\[['\"](.+?)['\"]\]$/);return m?m[1]:t;}
  function formatDate(v){if(!v)return "Date unavailable";var d=new Date(v);return Number.isNaN(d.getTime())?String(v):d.toLocaleDateString(undefined,{year:"numeric",month:"short",day:"numeric"});}
  function readTime(w){w=Number(w);return (!Number.isFinite(w)||w<=0)?null:Math.max(1,Math.ceil(w/220));}
  function normalizeArticle(a,i){var sr=String(a.source||"unknown").trim();return {id:a.article_id||a.url||(sr+"-"+(a.title||"")+"-"+i),category:String(a.category||"").trim(),src:SOURCE_KEYS[sr.toLowerCase()]||"medium",sourceLabel:SOURCE_LABELS[sr.toLowerCase()]||sr||"Unknown source",title:a.title||"Untitled article",author:normalizeAuthor(a.author),dateRaw:a.publication_date||null,date:formatDate(a.publication_date),description:a.description||"",url:a.url||"",tags:a.tags||"",content:a.content||"",wordCount:a.word_count,read:readTime(a.word_count)};}
  function catLabel(k){return CATEGORIES.find(function(c){return c.key===k;})||{label:k,tag:k};}

  var chipsEl=document.getElementById("chips");
  CATEGORIES.forEach(function(c){var b=document.createElement("button");b.className="chip";b.type="button";b.textContent=c.label;b.dataset.cat=c.key;b.addEventListener("click",function(){state.view="browse";state.category=c.key;state.query="";document.getElementById("searchInput").value="";render();});chipsEl.appendChild(b);});
  var navButtons=document.querySelectorAll("#nav button");
  navButtons.forEach(function(b){b.addEventListener("click",function(){state.view=b.dataset.view==="categories"?"browse":b.dataset.view;if(state.view==="browse"){state.query="";document.getElementById("searchInput").value="";}render();});});
  function runSearch(){state.query=document.getElementById("searchInput").value.trim();state.view=state.query?"search":"browse";render();}
  document.getElementById("searchBtn").addEventListener("click",runSearch);
  document.getElementById("searchInput").addEventListener("keydown",function(e){if(e.key==="Enter")runSearch();});
  document.getElementById("viewAllBtn").style.display="none";

  function cardHTML(a){var c=catLabel(a.category),isSaved=saved.has(a.id),read=a.read?a.read+" min read":(a.wordCount?Number(a.wordCount).toLocaleString()+" words":"");return '<article class="card"><div class="card-top"><span class="src-badge" style="background:var(--src-'+a.src+'-bg); color:var(--src-'+a.src+'-text)">'+escapeHtml(a.sourceLabel)+'</span><span class="meta-right"><span class="readtime">'+escapeHtml(read)+'</span><button class="save-btn" aria-pressed="'+isSaved+'" aria-label="Save article" data-id="'+escapeHtml(a.id)+'">'+(isSaved?'★':'☆')+'</button></span></div><h3><button class="article-link article-open" type="button" data-id="'+escapeHtml(a.id)+'">'+escapeHtml(a.title)+'</button></h3><p class="byline">By '+escapeHtml(a.author)+' · '+escapeHtml(a.date)+'</p>'+(a.description?'<p class="description">'+escapeHtml(a.description)+'</p>':'')+'<div class="card-foot"><span class="article-meta">'+(a.wordCount?Number(a.wordCount).toLocaleString()+' words':'Educational article')+'</span><span class="topic-badge">'+escapeHtml(c.tag)+'</span></div></article>';}
  function contentHTML(content){if(!content)return '<p class="article-empty">Full content is not available for this record.</p>';return escapeHtml(content).replace(/\r\n/g,"\n").replace(/\r/g,"\n").split(/\n{2,}/).map(function(b){return '<p>'+b.replace(/\n/g,'<br>')+'</p>';}).join('');}
  function articleReaderHTML(a){var c=catLabel(a.category),read=a.read?a.read+" min read":(a.wordCount?Number(a.wordCount).toLocaleString()+" words":""),original=a.url?'<a class="original-btn" href="'+escapeHtml(a.url)+'" target="_blank" rel="noopener noreferrer">View original article ↗</a>':'';return '<article class="article-reader"><button class="back-btn" id="backToBrowse" type="button">← Back to articles</button><div class="reader-head"><div class="reader-badges"><span class="src-badge" style="background:var(--src-'+a.src+'-bg); color:var(--src-'+a.src+'-text)">'+escapeHtml(a.sourceLabel)+'</span><span class="topic-badge">'+escapeHtml(c.tag)+'</span></div><h1>'+escapeHtml(a.title)+'</h1><p class="reader-byline">By '+escapeHtml(a.author)+' · '+escapeHtml(a.date)+(read?' · '+escapeHtml(read):'')+'</p>'+(a.description?'<p class="reader-description">'+escapeHtml(a.description)+'</p>':'')+'</div><div class="reader-content">'+contentHTML(a.content)+'</div><div class="reader-actions"><button class="back-btn" id="backToBrowseBottom" type="button">← Back</button>'+original+'</div></article>';}
  function paginationHTML(){if(state.totalPages<=1)return "";return '<div class="pagination"><button id="prevPage" '+(state.page<=1?'disabled':'')+'>← Previous</button><span>Page <strong>'+state.page.toLocaleString()+'</strong> of '+state.totalPages.toLocaleString()+'</span><button id="nextPage" '+(state.page>=state.totalPages?'disabled':'')+'>Next →</button></div>';}

  async function openArticle(id){state.articleId=id;state.view="article";state.loading=true;state.error="";currentArticle=null;render();window.scrollTo({top:0,behavior:"smooth"});try{var r=await fetch(API_URL+"/"+encodeURIComponent(id));if(!r.ok)throw new Error("HTTP "+r.status);currentArticle=normalizeArticle(await r.json(),0);state.loading=false;}catch(e){state.loading=false;state.error="Could not load this article from the TechHub API.";console.error(e);}render();}

  function render(){
    navButtons.forEach(function(b){b.setAttribute("aria-current",state.view===b.dataset.view?"page":"false");});
    chipsEl.querySelectorAll(".chip").forEach(function(b){b.setAttribute("aria-pressed",state.view==="browse"&&b.dataset.cat===state.category?"true":"false");});
    chipsEl.style.display=state.view==="browse"?"flex":"none";
    var title=document.getElementById("sectionTitle"),infoBox=document.getElementById("infoBox"),grid=document.getElementById("grid"),empty=document.getElementById("emptyState");
    document.querySelectorAll(".pagination").forEach(function(x){x.remove();});
    if(state.loading){title.textContent=state.view==="article"?"Loading article…":"Loading Gold articles…";infoBox.hidden=true;grid.innerHTML="";empty.hidden=false;empty.textContent="Loading from the TechHub API…";return;}
    if(state.error){title.textContent="Could not load data";infoBox.hidden=true;grid.innerHTML="";empty.hidden=false;empty.textContent=state.error;return;}
    if(state.view==="article"){
      chipsEl.style.display="none";title.textContent="Article";infoBox.hidden=true;empty.hidden=true;grid.innerHTML=currentArticle?articleReaderHTML(currentArticle):'<div class="empty">Article not found.</div>';
      function back(){state.view="browse";state.articleId=null;currentArticle=null;render();}
      var bt=document.getElementById("backToBrowse"),bb=document.getElementById("backToBrowseBottom");if(bt)bt.addEventListener("click",back);if(bb)bb.addEventListener("click",back);return;
    }
    var list=ARTICLES.slice();
    if(state.view==="search"){var q=state.query.toLowerCase();list=list.filter(function(a){return [a.title,a.author,a.description,a.tags,a.sourceLabel,a.category].join(" ").toLowerCase().indexOf(q)!==-1;});title.textContent='Search results on page '+state.page+' for "'+state.query+'"';infoBox.hidden=true;}
    else if(state.view==="saved"){list=list.filter(function(a){return saved.has(a.id);});title.textContent="Saved articles on this page";infoBox.hidden=true;}
    else if(state.view==="top"){title.textContent="Newest articles";infoBox.hidden=false;}
    else {list=list.filter(function(a){return a.category.toLowerCase()===state.category.toLowerCase();});title.textContent=catLabel(state.category).label+" articles on page "+state.page;infoBox.hidden=false;}
    if(!list.length){grid.innerHTML="";empty.hidden=false;empty.textContent="No matching articles on this page.";}else{empty.hidden=true;grid.innerHTML=list.map(cardHTML).join("");}
    grid.querySelectorAll(".save-btn").forEach(function(btn){btn.addEventListener("click",function(){var id=btn.dataset.id;if(saved.has(id))saved.delete(id);else saved.add(id);persistSaved();render();});});
    grid.querySelectorAll(".article-open").forEach(function(btn){btn.addEventListener("click",function(){openArticle(btn.dataset.id);});});
    var p=document.createElement("div");p.innerHTML=paginationHTML();if(p.firstChild){grid.insertAdjacentElement("afterend",p.firstChild);var prev=document.getElementById("prevPage"),next=document.getElementById("nextPage");if(prev)prev.addEventListener("click",function(){loadPage(state.page-1);});if(next)next.addEventListener("click",function(){loadPage(state.page+1);});}
  }

  async function loadPage(page){state.loading=true;state.error="";state.page=page;render();try{var r=await fetch(API_URL+"?page="+page+"&limit="+PAGE_SIZE);if(!r.ok)throw new Error("HTTP "+r.status);var data=await r.json();if(!data||!Array.isArray(data.articles))throw new Error("Unexpected API response");ARTICLES=data.articles.map(normalizeArticle);state.page=data.page||page;state.total=Number(data.total||0);state.totalPages=Number(data.total_pages||1);state.loading=false;window.scrollTo({top:0,behavior:"smooth"});}catch(e){state.loading=false;state.error="Could not connect to the TechHub API. Make sure FastAPI is running at 127.0.0.1:8000.";console.error(e);}render();}

  render();loadPage(1);
})();
