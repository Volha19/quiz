<script>
  import './home.css';
  import { onMount } from 'svelte';
  import QuizCalendar from '$lib/QuizCalendar.svelte';

  let loggedIn = false;
  let checking = true;
  let quizzes = [];
  let loadingQuizzes = false;
  let stats = {
    totalQuizzes: 0,
    totalAttempts: 0,
    averageScore: 0,
    bestScore: 0
  };
  
  let pieChart = null;
  let barChart = null;
  let chartData = {
    quizAttempts: [],
    quizScores: []
  };

  onMount(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      loggedIn = false;
      checking = false;
      return;
    }
    // Validate token with a lightweight authenticated request
    try {
      const res = await fetch('http://localhost:8000/api/quizzes/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      loggedIn = res.ok;
      
      if (loggedIn) {
        await fetchUserQuizzes(token);
        await fetchStatistics(token);
        await fetchChartData(token);
        setTimeout(() => {
          renderCharts();
        }, 100);
      }
    } catch {
      loggedIn = false;
    } finally {
      checking = false;
    }
  });

  const fetchUserQuizzes = async (token) => {
    loadingQuizzes = true;
    try {
      const res = await fetch('http://localhost:8000/api/quizzes/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        quizzes = await res.json();
      }
    } catch {
      console.error('Failed to fetch quizzes');
    } finally {
      loadingQuizzes = false;
    }
  };

  const fetchStatistics = async (token) => {
    try {
      const res = await fetch('http://localhost:8000/api/quizzes/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const userQuizzes = await res.json();
        stats.totalQuizzes = userQuizzes.length;
        
        // Fetch statistics from the new statistics endpoint
        try {
          const statsRes = await fetch('http://localhost:8000/api/statistics/', {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (statsRes.ok) {
            const statistics = await statsRes.json();
            stats.totalAttempts = statistics.length;
            
            if (statistics.length > 0) {
              let totalScore = 0;
              let maxScore = 0;
              statistics.forEach(stat => {
                totalScore += stat.score;
                maxScore = Math.max(maxScore, stat.score);
              });
              stats.averageScore = Math.round(totalScore / statistics.length);
              stats.bestScore = Math.round(maxScore);
            }
          }
        } catch (err) {
          console.log('Statistics endpoint not available:', err);
        }
      }
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
    }
  };

  const fetchChartData = async (token) => {
    try {
      const statsRes = await fetch('http://localhost:8000/api/statistics/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (statsRes.ok) {
        const statistics = await statsRes.json();
        
        // Count attempts per quiz
        const quizAttemptsMap = {};
        const quizScoresMap = {};
        
        statistics.forEach(stat => {
          const quizTitle = stat.quiz_title || 'Unknown Quiz';
          
          // Count attempts
          if (!quizAttemptsMap[quizTitle]) {
            quizAttemptsMap[quizTitle] = 0;
          }
          quizAttemptsMap[quizTitle]++;
          
          // Average scores per quiz
          if (!quizScoresMap[quizTitle]) {
            quizScoresMap[quizTitle] = { total: 0, count: 0 };
          }
          quizScoresMap[quizTitle].total += stat.score;
          quizScoresMap[quizTitle].count++;
        });
        
        // Convert to arrays for charts
        chartData.quizAttempts = Object.entries(quizAttemptsMap).map(([title, count]) => ({
          title,
          count
        }));
        
        chartData.quizScores = Object.entries(quizScoresMap).map(([title, data]) => ({
          title,
          averageScore: Math.round(data.total / data.count)
        }));
      }
    } catch (error) {
      console.error('Failed to fetch chart data:', error);
    }
  };

  const renderCharts = () => {
    // Destroy existing charts
    if (pieChart) pieChart.destroy();
    if (barChart) barChart.destroy();
    
    // Render Pie Chart - Quiz Attempts Distribution
    const pieCtx = document.getElementById('attemptsChart');
    if (pieCtx && chartData.quizAttempts.length > 0) {
      pieChart = new Chart(pieCtx, {
        type: 'pie',
        data: {
          labels: chartData.quizAttempts.map(q => q.title),
          datasets: [{
            data: chartData.quizAttempts.map(q => q.count),
            backgroundColor: [
              '#b290f5',
              '#8B7DC7',
              '#9B6B9E',
              '#7ecef3',
              '#6B8BC7',
              '#A48AD3'
            ]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                boxWidth: 12,
                padding: 10,
                font: { size: 11 }
              }
            },
            title: {
              display: true,
              text: 'Quiz Attempts Distribution',
              font: { size: 16, weight: 'bold' }
            }
          }
        }
      });
    }
    
    // Render Bar Chart - Average Scores per Quiz
    const barCtx = document.getElementById('scoresChart');
    if (barCtx && chartData.quizScores.length > 0) {
      barChart = new Chart(barCtx, {
        type: 'bar',
        data: {
          labels: chartData.quizScores.map(q => q.title),
          datasets: [{
            label: 'Average Score (%)',
            data: chartData.quizScores.map(q => q.averageScore),
            backgroundColor: '#9B6B9E',
            borderColor: '#68318d',
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              ticks: {
                callback: function(value) {
                  return value + '%';
                }
              }
            }
          },
          plugins: {
            legend: {
              display: false
            },
            title: {
              display: true,
              text: 'Average Score per Quiz',
              font: { size: 16, weight: 'bold' }
            }
          }
        }
      });
    }
  };

  const handleCreateQuiz = () => {
    const token = localStorage.getItem('access_token');
    if (!token || !loggedIn) {
      window.location.href = '/login';
    } else {
      window.location.href = '/upload';
    }
  };

  const handleTakeQuiz = (quizId) => {
    window.location.href = `/test_type/${quizId}`;
  };

  const handleExportPDF = async (quiz) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`http://localhost:8000/api/quizzes/${quiz.id}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const fullQuiz = await res.json();
      
      // Create PDF content
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF();
      
      // Set up document
      doc.setFontSize(16);
      doc.text(quiz.title, 10, 10);
      
      doc.setFontSize(10);
      doc.text(`Created: ${new Date(quiz.created_at).toLocaleDateString()}`, 10, 20);
      
      let yPosition = 30;
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 10;
      const maxWidth = 190;
      
      // Add questions
      if (fullQuiz.questions && Array.isArray(fullQuiz.questions)) {
        fullQuiz.questions.forEach((q, idx) => {
          // Check if we need a new page
          if (yPosition > pageHeight - 20) {
            doc.addPage();
            yPosition = 10;
          }
          
          doc.setFontSize(11);
          doc.setFont(undefined, 'bold');
          const questionText = `${idx + 1}. ${q.question_text}`;
          const wrappedQuestion = doc.splitTextToSize(questionText, maxWidth);
          doc.text(wrappedQuestion, margin, yPosition);
          yPosition += wrappedQuestion.length * 5 + 3;
          
          doc.setFont(undefined, 'normal');
          doc.setFontSize(10);
          
          if (q.options && Array.isArray(q.options)) {
            q.options.forEach((opt) => {
              if (yPosition > pageHeight - 15) {
                doc.addPage();
                yPosition = 10;
              }
              const optionText = `• ${opt.option_text}`;
              const wrappedOption = doc.splitTextToSize(optionText, maxWidth - 5);
              doc.text(wrappedOption, margin + 5, yPosition);
              yPosition += wrappedOption.length * 4 + 2;
            });
          }
          
          yPosition += 3;
        });
      }
      
      // Download
      doc.save(`${quiz.title}.pdf`);
    } catch (error) {
      console.error('Failed to export PDF:', error);
      alert('Failed to export quiz to PDF');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/';
  };
</script>

<svelte:head>
  <title>Quiz Maker - Home</title>
</svelte:head>

<main style="width: 100%; min-height: 100vh; padding: 40px 20px;">
  <div class="container">
    <!-- Header -->
    <header class="header">
      <div class="brand">
        <span>THE BEST</span>
        <span style="color: var(--color-primary);">Quiz Maker</span>
      </div>
      <div style="display:flex; align-items:center; gap:12px;">
        <span style="font-size:0.9rem; color: var(--color-text-secondary);">
        </span>
        <button on:click={handleCreateQuiz} class="cta-btn">
          Generate Quiz
        </button>
        {#if loggedIn}
          <button on:click={handleLogout} class="logout-btn">
            Logout
          </button>
        {/if}
      </div>
    </header>

    {#if loggedIn}
      <!-- Statistics & Analytics Section -->
      <section class="stats-section">
        <h2>Statistics & Analytics</h2>
        
        <div class="stats-grid">
          <div class="stat-card stat-card-1">
            <div class="stat-icon"><i class="bi bi-journal-text"></i></div>
            <div class="stat-content">
              <div class="stat-value">{stats.totalQuizzes}</div>
              <div class="stat-label">Quizzes Created</div>
            </div>
          </div>
          
          <div class="stat-card stat-card-2">
            <div class="stat-icon"><i class="bi bi-check-circle"></i></div>
            <div class="stat-content">
              <div class="stat-value">{stats.totalAttempts}</div>
              <div class="stat-label">Quiz Attempts</div>
            </div>
          </div>
          
          <div class="stat-card stat-card-3">
            <div class="stat-icon"><i class="bi bi-graph-up"></i></div>
            <div class="stat-content">
              <div class="stat-value">{stats.averageScore}%</div>
              <div class="stat-label">Average Score</div>
            </div>
          </div>
          
          <div class="stat-card stat-card-4">
            <div class="stat-icon"><i class="bi bi-trophy"></i></div>
            <div class="stat-content">
              <div class="stat-value">{stats.bestScore}%</div>
              <div class="stat-label">Best Score</div>
            </div>
          </div>
        </div>

        <!-- Charts -->
        {#if chartData.quizAttempts.length > 0 || chartData.quizScores.length > 0}
          <div class="charts-grid">
            {#if chartData.quizAttempts.length > 0}
              <div class="chart-container">
                <canvas id="attemptsChart"></canvas>
              </div>
            {/if}
            
            {#if chartData.quizScores.length > 0}
              <div class="chart-container">
                <canvas id="scoresChart"></canvas>
              </div>
            {/if}
          </div>
        {/if}

        <!-- Quiz Activity Calendar -->
        <QuizCalendar />
      </section>

      <!-- User Quizzes Section -->
      <section class="my-quizzes-section">
        <h2>My Quizzes</h2>
        {#if loadingQuizzes}
          <p style="text-align: center; color: var(--color-text-secondary);">Loading your quizzes...</p>
        {:else if quizzes && quizzes.length > 0}
          <div class="quizzes-grid">
            {#each quizzes as quiz (quiz.id)}
              <div class="quiz-item-card">
                <div class="quiz-item-header">
                  <h3>{quiz.title}</h3>
                  <span class="quiz-date">{new Date(quiz.created_at).toLocaleDateString()}</span>
                </div>
                <div class="quiz-item-content">
                  <p class="quiz-description">{quiz.extracted_text.substring(0, 100)}...</p>
                  <div class="quiz-item-footer">
                    <button on:click={() => handleExportPDF(quiz)} class="export-btn" title="Export to PDF">
                      <i class="bi bi-upload"></i>
                    </button>
                    <button on:click={() => handleTakeQuiz(quiz.id)} class="take-quiz-btn">
                      Take Quiz
                    </button>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div style="text-align: center; padding: 40px 20px; color: var(--color-text-secondary);">
            <p>No quizzes yet. Create one to get started!</p>
          </div>
        {/if}
      </section>
    {/if}

    <!-- Hero Section (show when not logged in) -->
    {#if !loggedIn}
      <section class="hero">
        <h1>Build Quizzes that Engage</h1>
        <p>Upload PDF or JPG files and automatically generate interactive quizzes from the content.</p>
      </section>

      <!-- Feature Cards -->
      <div class="card-grid">
        <div class="quiz-card card-1">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin: 0 auto 15px; display: block;">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
          <h3>PDF Upload</h3>
          <p>Extract text from PDF documents automatically.</p>
        </div>

        <div class="quiz-card card-2">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin: 0 auto 15px; display: block;">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
          <h3>Image OCR</h3>
          <p>Scan text from JPG and PNG images.</p>
        </div>

        <div class="quiz-card card-3">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin: 0 auto 15px; display: block;">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
          <h3>Smart Generation</h3>
          <p>AI-powered quiz question creation.</p>
        </div>

        <div class="quiz-card card-4">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin: 0 auto 15px; display: block;">
            <path d="M9 11l3 3L22 4"></path>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
          </svg>
          <h3>Interactive Quiz</h3>
          <p>Take quizzes with instant feedback.</p>
        </div>

        <div class="quiz-card card-5">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin: 0 auto 15px; display: block;">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
          <h3>Results & Review</h3>
          <p>Review answers with detailed explanations.</p>
        </div>
      </div>
    {/if}
  </div>
</main>
