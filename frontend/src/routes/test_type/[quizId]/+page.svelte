<script>
  import { onMount } from 'svelte';
  import '../test_type.css';

  export let params;

  let loading = true;
  let error = '';
  let topics = [];
  let quizTitle = '';

  let currentIndex = 0;
  let selected = null;
  let results = {};
  let showModal = false;
  let finished = false;
  let total = 0;
  let dark = false;

  const mapQuestionsToTopics = (questions = []) => {
    return questions.map((q) => ({
      title: q.question_text,
      type: q.question_type || 'multiple_choice',
      correctAnswer: q.correct_answer,
      correctAnswerText: q.correct_answer_text,
      answers: (q.options || []).map((opt, idx) => ({
        text: opt.option_text ?? opt.text ?? String(opt),
        value: opt.option_order ?? opt.value ?? idx
      }))
    }));
  };

  function setSelectedForCurrent() {
    const current = topics[currentIndex];
    const stored = results[currentIndex];
    if (current && current.type === 'open') {
      selected = stored ?? '';
    } else {
      selected = stored ?? null;
    }
  }

  const fetchQuiz = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      window.location.href = '/login';
      return;
    }

    const res = await fetch(`http://localhost:8000/api/quizzes/${params.quizId}/`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    const data = await res.json();

    if (!res.ok) {
      if (res.status === 401) {
        window.location.href = '/login';
        return;
      }
      throw new Error(data.detail || data.error || 'Failed to load quiz.');
    }

    quizTitle = data.title || 'Generated Quiz';
    topics = mapQuestionsToTopics(data.questions || []);

    if (!topics.length) {
      throw new Error('No generated questions found for this quiz.');
    }

    setSelectedForCurrent();
  };

  onMount(async () => {
    try {
      await fetchQuiz();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });

  const handleNext = async () => {
    if (!topics.length) return;

    const current = topics[currentIndex];
    const isOpen = current.type === 'open';
    const noSelection = isOpen ? !selected || !String(selected).trim() : selected === null;

    if (noSelection) {
      showModal = true;
      return;
    }

    // Store the selected answer (option_order value)
    results[currentIndex] = selected;

    if (currentIndex < topics.length - 1) {
      currentIndex += 1;
      setSelectedForCurrent();
      
    } else {
      finished = true;
      // Calculate score: count how many answers match correct_answer
      total = calculateScore();
      
      // Submit quiz results to backend
      await submitQuizResults();
    }
  };

  const submitQuizResults = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      // Prepare answers data - map question indices to answer values
      const answersData = {};
      topics.forEach((topic, idx) => {
        if (results[idx] !== undefined) {
          answersData[idx] = results[idx];
        }
      });

      await fetch(`http://localhost:8000/api/quizzes/${params.quizId}/submit/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          answers: answersData,
          score: total,
          total_questions: topics.length
        })
      });
    } catch (error) {
      console.error('Failed to submit quiz results:', error);
    }
  };

  const handleBack = () => {
    if (!topics.length) return;

    if (currentIndex > 0) {
      currentIndex -= 1;
      setSelectedForCurrent();
    }
  };

  const calculateScore = () => {
    let correctCount = 0;
    for (let i = 0; i < topics.length; i++) {
      const topic = topics[i];
      const userAnswer = results[i];

      if (topic.type === 'open') {
        if (topic.correctAnswerText && userAnswer !== undefined) {
          const normalize = (v) => String(v).trim().toLowerCase();
          if (normalize(userAnswer) === normalize(topic.correctAnswerText)) {
            correctCount++;
          }
        }
      } else {
        if (userAnswer !== undefined && userAnswer === topic.correctAnswer) {
          correctCount++;
        }
      }
    }
    return correctCount;
  };

  const getResultPercentage = () => {
    return Math.round((total / topics.length) * 100);
  };

  const getResultGif = () => {
    const percentage = getResultPercentage();
    
    if (percentage === 100) {
      return 'https://media.giphy.com/media/g9582DNuQppxC/giphy.gif'; // Perfect score celebration
    } else if (percentage >= 80) {
      return 'https://media.giphy.com/media/26u4cqiYI30juCOGY/giphy.gif'; // Great job
    } else if (percentage >= 60) {
      return 'https://media.giphy.com/media/3o7btNhMBytxAM6YBa/giphy.gif'; // Good effort
    } else if (percentage >= 40) {
      return 'https://media.giphy.com/media/d2lcHJTG5Tscg/giphy.gif'; // Keep trying
    } else {
      return 'https://media.giphy.com/media/ISOckXUybVfQ4/giphy.gif'; // Need more practice
    }
  };

  const getResultTitle = () => {
    const percentage = getResultPercentage();
    
    if (percentage === 100) {
      return '🏆 Perfect Score!';
    } else if (percentage >= 80) {
      return '🌟 Excellent Work!';
    } else if (percentage >= 60) {
      return '👍 Good Job!';
    } else if (percentage >= 40) {
      return '💪 Keep Practicing!';
    } else {
      return '📚 Room for Improvement';
    }
  };

  const getResultMessage = () => {
    const percentage = getResultPercentage();
    const correct = total;
    const incorrect = topics.length - total;
    
    if (percentage === 100) {
      return `Outstanding! You answered all ${topics.length} questions correctly! You have a deep understanding of this material. Your dedication and knowledge shine through brilliantly! 🎉`;
    } else if (percentage >= 80) {
      return `Impressive performance! You got ${correct} out of ${topics.length} questions right. You clearly have a strong grasp of the material. Just a bit more review and you'll be at the top! 🚀`;
    } else if (percentage >= 60) {
      return `Nice work! You answered ${correct} questions correctly. You're on the right track and showing good understanding. Keep studying and you'll improve even more! 📈`;
    } else if (percentage >= 40) {
      return `You got ${correct} correct answers. There's definitely potential here! Consider reviewing the material more thoroughly. With focused practice, you'll see significant improvement. Don't give up! 💡`;
    } else {
      return `You answered ${correct} out of ${topics.length} correctly. This topic seems challenging for you right now. Take time to review the material carefully, perhaps try different learning resources. Everyone learns at their own pace - keep going! 🌱`;
    }
  };

  const closeModal = () => {
    showModal = false;
  };

  const toggleDark = () => {
    dark = !dark;
    if (dark) {
      document.body.classList.add('dark-mode-variables');
    } else {
      document.body.classList.remove('dark-mode-variables');
    }
  };

  $: progress = finished
    ? 100
    : topics.length
      ? (currentIndex / topics.length) * 100
      : 0;


</script>

<svelte:head>
  <title>{quizTitle ? `${quizTitle} — Quiz Maker` : 'Quiz — Quiz Maker'}</title>
  <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Sharp" rel="stylesheet" />
</svelte:head>

<div class="page" class:dark={dark}>
  <div class="container">
    <header class="header">
      <div class="logo">
        <h2>{quizTitle || 'Loading quiz...'}</h2>
      </div>
      <button class="dark-mode" type="button" on:click={toggleDark} aria-label="Toggle theme">
        <span class:active={!dark} class="material-icons-sharp">light_mode</span>
        <span class:active={dark} class="material-icons-sharp">dark_mode</span>
      </button>
    </header>

    {#if loading}
      <main class="page__container">
        <div class="container_form">
          <div class="board">
            <p>Loading generated questions...</p>
          </div>
        </div>
      </main>
    {:else if error}
      <main class="page__container">
        <div class="container_form">
          <div class="board">
            <h1 class="board-header">Error</h1>
            <p>{error}</p>
          </div>
        </div>
      </main>
    {:else}
      <main class="page__container">
        <div class="container_form">
          <div class="header_form">
            <div class="progress-bar-container">
              <div class="progress-bar">
                <div class="progress" style={`width: ${progress}%`}></div>
              </div>
            </div>
            <p class="question-counter">Question {currentIndex + 1} of {topics.length}</p>
          </div>

          {#if !finished}
            <div class="board">
              <h1 class="board-header">{topics[currentIndex].title}</h1>
              {#if topics[currentIndex].type === 'open'}
                <div class="blocks_card">
                  <h2 class="text">Enter your answer:</h2>
                  <textarea
                    class="open-input"
                    rows="4"
                    bind:value={selected}
                    placeholder="Type your answer here"
                  ></textarea>
                </div>
              {:else}
                <div class="blocks_card">
                  <h2 class="text">Select an answer option:</h2>
                  <div class="checklist">
                    {#each topics[currentIndex].answers as ans}
                      <label class="check-item">
                        <input
                          type="radio"
                          name={`variant-${currentIndex}`}
                          value={ans.value}
                          checked={selected === ans.value}
                          on:change={() => (selected = ans.value)}
                        />
                        <span>{ans.text}</span>
                      </label>
                    {/each}
                  </div>
                </div>
              {/if}
              <footer class="footer">
                <div class="footer-items-container">
                  <div class="item left">
                    <button class="skip-button" on:click={handleBack} disabled={currentIndex === 0}>Back</button>
                  </div>
                  <div class="item right">
                    <button class="check-button" on:click={handleNext}>
                      {currentIndex === topics.length - 1 ? 'Results' : 'Next'}
                    </button>
                  </div>
                </div>
              </footer>
            </div>
          {:else}
            <div class="board">
              <h1 class="board-header">Quiz Results</h1>
              <div class="result-box">
                <div class="score-display">
                  <div class="score-card">
                    <div class="score-title">Your Score</div>
                    <div class="score-main">{total}</div>
                    <div class="score-sub">of {topics.length}</div>
                  </div>
                  <div class="score-card">
                    <div class="score-title">Percentage</div>
                    <div class="score-main">{Math.round((total / topics.length) * 100)}%</div>
                    <div class="score-sub">based on {topics.length} questions</div>
                  </div>
                </div>
                
                <div class="result-analysis">
                  <div class="gif-container">
                    <img src={getResultGif()} alt="Result reaction" class="result-gif" />
                  </div>
                  <div class="analysis-text">
                    <h3>{getResultTitle()}</h3>
                    <p>{getResultMessage()}</p>
                  </div>
                </div>
                
                <div class="result-footer">
                  <button class="back-to-quizzes-btn" on:click={() => window.location.href = '/'}>
                    Back to My Quizzes
                  </button>
                </div>
              </div>
            </div>
          {/if}
        </div>
      </main>

      {#if showModal}
        <div class="modal" role="alertdialog">
          <div class="modal-content">
            <p>You did not select an answer option!</p>
            <button id="modalClose" on:click={closeModal}>OK</button>
          </div>
        </div>
      {/if}
    {/if}
  </div>
</div>

