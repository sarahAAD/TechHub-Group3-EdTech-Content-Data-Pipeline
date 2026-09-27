(function(){
  var API_URL = "https://techhub-api.bravewater-78d0955a.uaenorth.azurecontainerapps.io/articles";
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
  var state = {view:"browse", category:null, query:"", loading:true, error:"", articleId:null, page:1, total:0, totalPages:1};
  // Saved articles are stored with their summary so they show up from any page
  var saved = new Map();
  try{ var raw=localStorage.getItem("techhub_saved"); if(raw) JSON.parse(raw).forEach(function(a){if(a&&typeof a==="object"&&a.id)saved.set(a.id,a);}); }catch(e){}
  function persistSaved(){ try{localStorage.setItem("techhub_saved",JSON.stringify(Array.from(saved.values())));}catch(e){} }
  function toggleSaved(id){if(saved.has(id)){saved.delete(id);}else{var a=ARTICLES.find(function(x){return x.id===id;})||(currentArticle&&currentArticle.id===id?currentArticle:null);if(a){var copy=Object.assign({},a);delete copy.content;saved.set(id,copy);}}persistSaved();}
  function escapeHtml(v){return String(v==null?"":v).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");}
  function normalizeAuthor(v){if(!v)return "Unknown";var t=String(v).trim(),m=t.match(/^\[['\"](.+?)['\"]\]$/);return m?m[1]:t;}
  function formatDate(v){if(!v)return "Date unavailable";var d=new Date(v);return Number.isNaN(d.getTime())?String(v):d.toLocaleDateString(undefined,{year:"numeric",month:"short",day:"numeric"});}
  function readTime(w){w=Number(w);return (!Number.isFinite(w)||w<=0)?null:Math.max(1,Math.ceil(w/220));}
  function normalizeArticle(a,i){var sr=String(a.source||"unknown").trim();return {id:a.article_id||a.url||(sr+"-"+(a.title||"")+"-"+i),category:String(a.category||"").trim(),src:SOURCE_KEYS[sr.toLowerCase()]||"medium",sourceLabel:SOURCE_LABELS[sr.toLowerCase()]||sr||"Unknown source",title:a.title||"Untitled article",author:normalizeAuthor(a.author),dateRaw:a.publication_date||null,date:formatDate(a.publication_date),description:a.description||"",url:a.url||"",tags:a.tags||"",content:a.content||"",wordCount:a.word_count,read:readTime(a.word_count)};}
  function catLabel(k){return CATEGORIES.find(function(c){return c.key===k;})||{label:k,tag:k};}

  var chipsEl=document.getElementById("chips");
  CATEGORIES.forEach(function(c){var b=document.createElement("button");b.className="chip";b.type="button";b.textContent=c.label;b.dataset.cat=c.key;b.addEventListener("click",function(){state.category=(state.category===c.key)?null:c.key;if(state.view!=="browse"&&state.view!=="categories")state.view="categories";state.query="";document.getElementById("searchInput").value="";loadPage(1);});chipsEl.appendChild(b);});
  var navButtons=document.querySelectorAll("#nav button");
  navButtons.forEach(function(b){b.addEventListener("click",function(){state.view=b.dataset.view;if(state.view==="browse")state.category=null;state.query="";document.getElementById("searchInput").value="";if(state.view==="saved")render();else loadPage(1);});});
  function runSearch(){state.query=document.getElementById("searchInput").value.trim();state.view=state.query?"search":"browse";loadPage(1);}
  document.getElementById("searchBtn").addEventListener("click",runSearch);
  document.getElementById("searchInput").addEventListener("keydown",function(e){if(e.key==="Enter")runSearch();});
  document.getElementById("viewAllBtn").style.display="none";

  function cardHTML(a){var c=catLabel(a.category),isSaved=saved.has(a.id),read=a.read?a.read+" min read":(a.wordCount?Number(a.wordCount).toLocaleString()+" words":"");return '<article class="card"><div class="card-top"><span class="src-badge" style="background:var(--src-'+a.src+'-bg); color:var(--src-'+a.src+'-text)">'+escapeHtml(a.sourceLabel)+'</span><span class="meta-right"><span class="readtime">'+escapeHtml(read)+'</span><button class="save-btn" aria-pressed="'+isSaved+'" aria-label="Save article" data-id="'+escapeHtml(a.id)+'">'+(isSaved?'★':'☆')+'</button></span></div><h3><button class="article-link article-open" type="button" data-id="'+escapeHtml(a.id)+'">'+escapeHtml(a.title)+'</button></h3><p class="byline">By '+escapeHtml(a.author)+' · '+escapeHtml(a.date)+'</p>'+(a.description?'<p class="description">'+escapeHtml(a.description)+'</p>':'')+'<div class="card-foot"><span class="article-meta">'+(a.wordCount?Number(a.wordCount).toLocaleString()+' words':'Educational article')+'</span><span class="topic-badge">'+escapeHtml(c.tag)+'</span></div></article>';}
  function contentHTML(content){if(!content)return '<p class="article-empty">Full content is not available for this record.</p>';return escapeHtml(content).replace(/\r\n/g,"\n").replace(/\r/g,"\n").split(/\n{2,}/).map(function(b){return '<p>'+b.replace(/\n/g,'<br>')+'</p>';}).join('');}
  function articleReaderHTML(a){var c=catLabel(a.category),read=a.read?a.read+" min read":(a.wordCount?Number(a.wordCount).toLocaleString()+" words":""),original=a.url?'<a class="original-btn" href="'+escapeHtml(a.url)+'" target="_blank" rel="noopener noreferrer">View original article ↗</a>':'';return '<article class="article-reader"><button class="back-btn" id="backToBrowse" type="button">← Back to articles</button><div class="reader-head"><div class="reader-badges"><span class="src-badge" style="background:var(--src-'+a.src+'-bg); color:var(--src-'+a.src+'-text)">'+escapeHtml(a.sourceLabel)+'</span><span class="topic-badge">'+escapeHtml(c.tag)+'</span></div><h1>'+escapeHtml(a.title)+'</h1><p class="reader-byline">By '+escapeHtml(a.author)+' · '+escapeHtml(a.date)+(read?' · '+escapeHtml(read):'')+'</p>'+(a.description?'<p class="reader-description">'+escapeHtml(a.description)+'</p>':'')+'</div><div class="reader-content">'+contentHTML(a.content)+'</div><div class="reader-actions"><button class="back-btn" id="backToBrowseBottom" type="button">← Back</button>'+original+'</div></article>';}
  function paginationHTML(){if(state.totalPages<=1)return "";return '<div class="pagination"><button id="prevPage" '+(state.page<=1?'disabled':'')+'>← Previous</button><span>Page <strong>'+state.page.toLocaleString()+'</strong> of '+state.totalPages.toLocaleString()+'</span><button id="nextPage" '+(state.page>=state.totalPages?'disabled':'')+'>Next →</button></div>';}

  async function openArticle(id){if(state.view!=="article")state.prevView=state.view;state.articleId=id;state.view="article";state.loading=true;state.error="";currentArticle=null;render();window.scrollTo({top:0,behavior:"smooth"});try{var r=await fetch(API_URL+"/"+encodeURIComponent(id));if(!r.ok)throw new Error("HTTP "+r.status);currentArticle=normalizeArticle(await r.json(),0);state.loading=false;}catch(e){state.loading=false;state.error="Could not load this article from the TechHub API.";console.error(e);}render();}

  function render(){
    navButtons.forEach(function(b){b.setAttribute("aria-current",state.view===b.dataset.view?"page":"false");});
    chipsEl.querySelectorAll(".chip").forEach(function(b){b.setAttribute("aria-pressed",(state.view==="browse"||state.view==="categories")&&b.dataset.cat===state.category?"true":"false");b.title=b.dataset.cat===state.category?"Click again to clear":"";});
    chipsEl.style.display=(state.view==="browse"||state.view==="categories")?"flex":"none";
    var title=document.getElementById("sectionTitle"),infoBox=document.getElementById("infoBox"),grid=document.getElementById("grid"),empty=document.getElementById("emptyState");
    document.querySelectorAll(".pagination").forEach(function(x){x.remove();});
    if(state.loading){title.textContent=state.view==="article"?"Loading article…":"Loading Gold articles…";infoBox.hidden=true;grid.innerHTML="";empty.hidden=false;empty.textContent="Loading from the TechHub API…";return;}
    if(state.error){title.textContent="Could not load data";infoBox.hidden=true;grid.innerHTML="";empty.hidden=false;empty.textContent=state.error;return;}
    if(state.view==="article"){
      chipsEl.style.display="none";title.textContent="Article";infoBox.hidden=true;empty.hidden=true;grid.innerHTML=currentArticle?articleReaderHTML(currentArticle):'<div class="empty">Article not found.</div>';
      function back(){state.view=state.prevView||"browse";state.articleId=null;currentArticle=null;render();}
      var bt=document.getElementById("backToBrowse"),bb=document.getElementById("backToBrowseBottom");if(bt)bt.addEventListener("click",back);if(bb)bb.addEventListener("click",back);return;
    }
    var list=ARTICLES.slice(),count=state.total.toLocaleString();
    if(state.view==="search"){title.textContent=count+' result'+(state.total===1?'':'s')+' for "'+state.query+'"';infoBox.hidden=true;}
    else if(state.view==="saved"){list=Array.from(saved.values());title.textContent="Saved articles ("+list.length+")";infoBox.hidden=true;}
    else if(state.view==="top"){title.textContent="Newest articles ("+count+")";infoBox.hidden=false;}
    else {title.textContent=(state.category?catLabel(state.category).label+" articles":(state.view==="categories"?"All categories — pick one above":"All articles"))+" ("+count+")";infoBox.hidden=false;}
    if(!list.length){grid.innerHTML="";empty.hidden=false;empty.textContent=state.view==="saved"?"You haven't saved any articles yet.":state.view==="search"?"No articles match that search — try a different keyword.":"No articles found.";}else{empty.hidden=true;grid.innerHTML=list.map(cardHTML).join("");}
    grid.querySelectorAll(".save-btn").forEach(function(btn){btn.addEventListener("click",function(){toggleSaved(btn.dataset.id);render();});});
    grid.querySelectorAll(".article-open").forEach(function(btn){btn.addEventListener("click",function(){openArticle(btn.dataset.id);});});
    var p=document.createElement("div");p.innerHTML=state.view==="saved"?"":paginationHTML();if(p.firstChild){grid.insertAdjacentElement("afterend",p.firstChild);var prev=document.getElementById("prevPage"),next=document.getElementById("nextPage");if(prev)prev.addEventListener("click",function(){loadPage(state.page-1);});if(next)next.addEventListener("click",function(){loadPage(state.page+1);});}
  }

  function listParams(page){
    var p=new URLSearchParams({page:String(page),limit:String(PAGE_SIZE)});
    if(state.view==="search"){p.set("q",state.query);p.set("sort","mixed");}
    else if(state.view==="top"){p.set("sort","newest");}
    else {if(state.category)p.set("category",state.category);p.set("sort","mixed");}
    return p.toString();
  }
  var loadSeq=0;
  async function loadPage(page){var seq=++loadSeq;state.loading=true;state.error="";state.page=page;render();try{var r=await fetch(API_URL+"?"+listParams(page));if(!r.ok){var detail="";try{detail=(await r.json()).detail||"";}catch(_){}throw new Error("HTTP "+r.status+(detail?" — "+detail:""));}var data=await r.json();if(seq!==loadSeq)return;if(!data||!Array.isArray(data.articles))throw new Error("Unexpected API response");ARTICLES=data.articles.map(normalizeArticle);state.page=data.page||page;state.total=Number(data.total||0);state.totalPages=Number(data.total_pages||1);state.loading=false;window.scrollTo({top:0,behavior:"smooth"});}catch(e){state.loading=false;state.error="Could not load articles from the TechHub API ("+(e&&e.message?e.message:e)+").";console.error(e);}render();}

  // Light / dark toggle
  var themeBtn=document.getElementById("themeBtn");
  function syncThemeBtn(){var dark=document.documentElement.getAttribute("data-theme")==="dark";themeBtn.textContent=dark?"☀️":"🌙";var l=dark?"Switch to light mode":"Switch to dark mode";themeBtn.setAttribute("aria-label",l);themeBtn.title=l;}
  if(themeBtn){syncThemeBtn();themeBtn.addEventListener("click",function(){var next=document.documentElement.getAttribute("data-theme")==="dark"?"light":"dark";document.documentElement.setAttribute("data-theme",next);try{localStorage.setItem("techhub_theme",next);}catch(e){}syncThemeBtn();});}

  render();loadPage(1);
})();
