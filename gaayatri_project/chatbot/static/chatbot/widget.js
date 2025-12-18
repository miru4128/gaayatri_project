// Chat widget JS: handle context intake, open/close panel, send messages to chatbot API, render messages
document.addEventListener('DOMContentLoaded', function(){
  const apiUrl = window.GAAYATRI_CHATBOT_API || '/chatbot/api/';
  const widget = document.getElementById('gaayatri-chat-widget');
  if(!widget) return;

  const bubble = widget.querySelector('.chat-bubble-btn');
  const panel = widget.querySelector('.chat-panel');
  const closeBtn = widget.querySelector('.chat-close');
  const messagesEl = widget.querySelector('.chat-body');
  const input = widget.querySelector('.chat-input');
  const sendBtn = widget.querySelector('.chat-send');
  const errorEl = widget.querySelector('.chat-error');
  const contextOverlay = widget.querySelector('.chat-context-overlay');
  const contextForm = widget.querySelector('.chat-context-form');
  const contextSummary = widget.querySelector('.chat-context-summary');
  const summaryText = contextSummary?.querySelector('.summary-text');
  const changeContextBtn = contextSummary?.querySelector('.chat-change-context');
  const cattleSelect = contextForm?.querySelector('.context-cattle-select');
  const manualName = contextForm?.querySelector('input[name=manual_name]');
  const manualBreed = contextForm?.querySelector('input[name=manual_breed]');
  const manualAge = contextForm?.querySelector('input[name=manual_age]');
  const manualMilk = contextForm?.querySelector('input[name=manual_milk]');
  const manualStage = contextForm?.querySelector('input[name=manual_stage]');
  const manualIssue = contextForm?.querySelector('textarea[name=manual_issue]');
  const contextError = contextForm?.querySelector('.context-error');

  let chatContext = null;
  let contextAcknowledged = false;

  function escapeHtml(str){
    return str.replace(/[&<>"']/g, function(c){
      switch(c){
        case '&': return '&amp;';
        case '<': return '&lt;';
        case '>': return '&gt;';
        case '"': return '&quot;';
        case "'": return '&#39;';
        default: return c;
      }
    });
  }

  function applyInlineFormatting(text){
    let escaped = escapeHtml(text);
    escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/\*(.+?)\*/g, '<em>$1</em>');
    escaped = escaped.replace(/`(.+?)`/g, '<code>$1</code>');
    return escaped;
  }

  function normalizeLine(line){
    let l = line.trim();
    l = l.replace(/^-\s*-\s*/, '- ');
    l = l.replace(/^\d+\.\s*-\s*/, '- ');
    return l;
  }

  function lineType(line){
    if(/^\d+\.\s+/.test(line)) return 'ordered';
    if(/^[-*]\s+/.test(line)) return 'unordered';
    return 'text';
  }

  function stripMarker(line){
    return line.replace(/^\d+\.\s+/, '').replace(/^[-*]\s+/, '');
  }

  function renderFormatted(text){
    if(!text) return '';
    const paragraphs = text.trim().split(/\n\n+/).filter(Boolean);
    const htmlParts = [];

    paragraphs.forEach(paragraph => {
      const rawLines = paragraph.split(/\n+/).map(normalizeLine).filter(Boolean);
      if(rawLines.length === 0) return;

      const types = rawLines.map(lineType);
      const isList = types.every(t => t !== 'text');
      if(isList){
        const useOrdered = types.every(t => t === 'ordered');
        const tag = useOrdered ? 'ol' : 'ul';
        const items = rawLines.map(line => {
          const content = stripMarker(line);
          return `<li>${applyInlineFormatting(content)}</li>`;
        }).join('');
        htmlParts.push(`<${tag}>${items}</${tag}>`);
      } else {
        const processed = rawLines.map(line => applyInlineFormatting(stripMarker(line))).join('<br>');
        htmlParts.push(`<p>${processed}</p>`);
      }
    });

    return htmlParts.join('');
  }

  function formatMessage(role, text, allowFeedback=true, extraClass){
    const d = document.createElement('div');
    d.className = 'message ' + (role==='user' ? 'user' : 'bot');
    if(extraClass){ d.classList.add(extraClass); }
    const b = document.createElement('div'); b.className = 'bubble'; b.innerHTML = renderFormatted(text);
    d.appendChild(b);
    if(role==='bot' && allowFeedback){
      const fb = document.createElement('div'); fb.className = 'feedback';
      fb.innerHTML = '<button class="fb-btn fb-up">👍</button> <button class="fb-btn fb-down">👎</button>';
      d.appendChild(fb);
    }
    return d;
  }

  function appendBot(text, allowFeedback=true, extraClass){
    const node = formatMessage('bot', text, allowFeedback, extraClass);
    messagesEl.appendChild(node);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    const fb = node.querySelector('.feedback');
    if(fb && node.dataset.msgId){
      fb.querySelector('.fb-up').addEventListener('click', ()=>sendFeedback(node.dataset.msgId, 1, fb));
      fb.querySelector('.fb-down').addEventListener('click', ()=>sendFeedback(node.dataset.msgId, -1, fb));
    }
    return node;
  }

  function disableInput(){
    if(input) input.disabled = true;
    if(sendBtn) sendBtn.disabled = true;
  }
  function enableInput(){
    if(input) input.disabled = false;
    if(sendBtn) sendBtn.disabled = false;
    input?.focus();
  }

  function buildContextSummary(ctx){
    if(!ctx) return '';
    const bits = [];
    if(ctx.name) bits.push(ctx.name);
    if(ctx.breed) bits.push(`${ctx.breed} breed`);
    if(ctx.age_years) bits.push(`${ctx.age_years} yrs`);
    if(ctx.milk_yield) bits.push(`${ctx.milk_yield} L/day`);
    if(ctx.issue) bits.push(`Issue: ${ctx.issue}`);
    return bits.join(', ') || 'Context saved';
  }

  function applyContext(ctx){
    chatContext = ctx;
    if(contextOverlay) contextOverlay.classList.add('hidden');
    if(summaryText) summaryText.textContent = buildContextSummary(ctx);
    if(contextSummary) contextSummary.classList.remove('chat-hidden');
    enableInput();
    if(!contextAcknowledged){
      appendBot('Thanks! I have your cattle details. How can I assist you today?', false, 'context-intro');
      contextAcknowledged = true;
    }
  }

  function clearFormErrors(){
    if(contextError){
      contextError.textContent = '';
      contextError.style.display = 'none';
    }
  }

  function showFormError(msg){
    if(contextError){
      contextError.textContent = msg;
      contextError.style.display = 'block';
    }
  }

  function resetContext(){
    chatContext = null;
    contextAcknowledged = false;
    if(contextSummary) contextSummary.classList.add('chat-hidden');
    if(contextOverlay) contextOverlay.classList.remove('hidden');
    clearFormErrors();
    if(cattleSelect) cattleSelect.value = '';
    if(manualName) manualName.value = '';
    if(manualBreed) manualBreed.value = '';
    if(manualAge) manualAge.value = '';
    if(manualMilk) manualMilk.value = '';
    if(manualStage) manualStage.value = '';
    if(manualIssue) manualIssue.value = '';
    disableInput();
  }

  function ensureContext(){
    if(chatContext) return true;
    if(contextOverlay) contextOverlay.classList.remove('hidden');
    disableInput();
    return false;
  }

  if(contextForm){
    disableInput();
    contextOverlay?.classList.remove('hidden');
    contextForm.addEventListener('submit', function(ev){
      ev.preventDefault();
      clearFormErrors();
      let ctx = {};
      const selected = cattleSelect && cattleSelect.value ? cattleSelect.options[cattleSelect.selectedIndex] : null;
      if(selected && selected.value){
        ctx = {
          source: 'saved',
          animal_id: selected.value,
          name: selected.dataset.name || '',
          tag_number: selected.dataset.tag || '',
          breed: selected.dataset.breed || '',
          age_years: selected.dataset.age || '',
          milk_yield: selected.dataset.yield || ''
        };
      } else {
        ctx = {
          source: 'manual',
          name: manualName?.value.trim(),
          breed: manualBreed?.value.trim(),
          age_years: manualAge?.value.trim(),
          milk_yield: manualMilk?.value.trim(),
          lactation_stage: manualStage?.value.trim(),
          issue: manualIssue?.value.trim()
        };
      }
      Object.keys(ctx).forEach(key => {
        const val = ctx[key];
        if(val === undefined || val === null || (typeof val === 'string' && !val.trim())){
          delete ctx[key];
        } else if(typeof val === 'string') {
          ctx[key] = val.trim();
        }
      });
      if(!ctx.breed && !ctx.issue && !ctx.name && !ctx.tag_number){
        showFormError('Please select a saved animal or share at least breed, name, or the current issue.');
        return;
      }
      applyContext(ctx);
    });
  }

  if(changeContextBtn){
    changeContextBtn.addEventListener('click', function(){
      resetContext();
    });
  }

  function openPanel(){
    panel.classList.remove('chat-hidden');
    bubble.style.display = 'none';
    if(chatContext){
      enableInput();
    } else {
      disableInput();
    }
  }
  function closePanel(){
    panel.classList.add('chat-hidden');
    bubble.style.display = 'inline-flex';
  }

  bubble?.addEventListener('click', openPanel);
  closeBtn?.addEventListener('click', closePanel);

  async function sendMessage(text){
    if(!text) return;
    if(!ensureContext()) return;
    errorEl.style.display='none';
    messagesEl.appendChild(formatMessage('user', text));
  const placeholder = formatMessage('bot', '...', false);
    messagesEl.appendChild(placeholder);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    try{
      const csrf = document.querySelector('input[name=csrfmiddlewaretoken]')?.value || (document.cookie.match(/(^| )csrftoken=([^;]+)/)?.[2] || '');
      const res = await fetch(apiUrl, {
        method: 'POST', credentials:'same-origin',
        headers: {'Content-Type':'application/json', 'X-CSRFToken': csrf},
        body: JSON.stringify({message: text, context: chatContext})
      });
      const json = await res.json();
      placeholder.remove();
      if(!res.ok || !json.ok){
        const errorMsg = json.error || json.reply || 'Error';
        appendBot(errorMsg);
        if(json.error === 'forbidden'){
          disableInput();
        }
      } else {
        const node = appendBot(json.reply || 'No reply');
        if(json.bot_message_id){
          node.dataset.msgId = json.bot_message_id;
          const fb = node.querySelector('.feedback');
          if(fb){
            fb.querySelector('.fb-up').addEventListener('click', ()=>sendFeedback(node.dataset.msgId, 1, fb));
            fb.querySelector('.fb-down').addEventListener('click', ()=>sendFeedback(node.dataset.msgId, -1, fb));
          }
        }
      }
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }catch(e){
      placeholder.remove();
      appendBot('Network error. Try again.');
    }
  }

  async function sendFeedback(messageId, value, container){
    if(!messageId) return;
    const csrf = document.querySelector('input[name=csrfmiddlewaretoken]')?.value || (document.cookie.match(/(^| )csrftoken=([^;]+)/)?.[2] || '');
    try{
      const res = await fetch('/chatbot/feedback/', {
        method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type':'application/json', 'X-CSRFToken': csrf},
        body: JSON.stringify({message_id: messageId, feedback: value})
      });
      const j = await res.json();
      if(res.ok && j.ok){
        container.innerHTML = (value===1) ? 'Thanks 👍' : 'Thanks 👎';
      } else {
        container.innerHTML = 'Feedback failed';
      }
    }catch(e){ container.innerHTML = 'Feedback error'; }
  }

  sendBtn?.addEventListener('click', function(){
    const t = input.value.trim();
    if(!t) return;
    input.value='';
    sendMessage(t);
  });
  input?.addEventListener('keydown', function(e){
    if(e.key==='Enter'){
      e.preventDefault();
      sendBtn.click();
    }
  });
});
