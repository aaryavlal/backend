// Minimal quiz frontend logic used by /quiz/<id> and /quizzes
async function fetchJson(url, opts){
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error('Request failed: '+r.status);
  return r.json();
}

window.loadQuiz = async function(quizId, container){
  try{
    const q = await fetchJson('/api/quiz/' + quizId);
    container.innerHTML = '';
    const title = document.createElement('h2');
    title.textContent = q.title;
    container.appendChild(title);
    const form = document.createElement('form');
    form.id = 'quiz-form';
    q.questions.forEach(question=>{
      const qdiv = document.createElement('div');
      qdiv.innerHTML = `<p><strong>${question.text}</strong></p>`;
      question.choices.forEach(choice=>{
        const id = `q${question.id}_c${choice.id}`;
        const label = document.createElement('label');
        label.innerHTML = `<input type='radio' name='q_${question.id}' value='${choice.id}' id='${id}'> ${choice.text}`;
        qdiv.appendChild(label);
      });
      form.appendChild(qdiv);
    });
    // allow optional local userId input for testing
    const userIdLabel = document.createElement('div');
    userIdLabel.innerHTML = `<label style="display:block;margin-bottom:8px">Test User ID (optional): <input id="_test_user_id" type="number" style="width:110px"></label>`;
    form.appendChild(userIdLabel);

    const submit = document.createElement('button');
    submit.type = 'button';
    submit.textContent = 'Submit';
    submit.addEventListener('click', async ()=>{
      const answers = [];
      q.questions.forEach(question=>{
        const sel = form.querySelector(`input[name='q_${question.id}']:checked`);
        if (sel) answers.push({questionId: question.id, choiceId: parseInt(sel.value)});
      });
      try{
        const payload = {quizId: q.id, answers: answers};
        const maybeUser = document.getElementById('_test_user_id') && document.getElementById('_test_user_id').value;
        if (maybeUser) payload.userId = parseInt(maybeUser);
        const res = await fetchJson('/api/quiz/attempt', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
        alert('Score: '+res.score + ' / ' + res.total);
        // refresh leaderboard on the same page if present
        const lb = document.getElementById('leaderboard-root');
        if (lb && window.loadLeaderboard) window.loadLeaderboard(q.id, lb);
      }catch(e){
        alert('Submit failed: '+e.message);
      }
    });
    form.appendChild(submit);
    container.appendChild(form);
  }catch(e){
    container.innerHTML = '<p>Failed to load quiz.</p>';
    console.error(e);
  }
}

// export helpers for page that lists quizzes
window.loadQuizList = async function(container){
  try{
    const data = await fetchJson('/api/quiz/all');
    container.innerHTML = '';
    data.forEach(q=>{
      const d = document.createElement('div');
      d.innerHTML = `<h3>${q.title}</h3><p>${q.description||''}</p><a href='/quiz/${q.id}'>Take Quiz</a> | <a href='/leaderboard/${q.id}'>Leaderboard</a>`;
      container.appendChild(d);
    });
  }catch(e){
    container.innerHTML = '<p>Failed to fetch quizzes.</p>';
  }
}


window.loadLeaderboard = async function(quizId, container){
  try{
    const data = await fetchJson('/api/quiz/leaderboard/'+quizId);
    container.innerHTML = '';
    const tbl = document.createElement('table');
    tbl.border = 1;
    const hdr = document.createElement('tr');
    hdr.innerHTML = '<th>Rank</th><th>User</th><th>Score</th><th>Total</th><th>When</th>';
    tbl.appendChild(hdr);
    data.forEach((row, idx)=>{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${idx+1}</td><td>${row.userName||row.userId}</td><td>${row.score}</td><td>${row.total}</td><td>${new Date(row.timestamp).toLocaleString()}</td>`;
      tbl.appendChild(tr);
    });
    container.appendChild(tbl);
  }catch(e){
    container.innerHTML = '<p>Failed to load leaderboard.</p>';
  }
}
