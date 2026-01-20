<script>
  import { onMount } from 'svelte';

  let calendarData = {};
  let currentDate = new Date();
  let selectedDate = null;
  let loading = true;
  
  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  onMount(async () => {
    await fetchCalendarData();
  });

  const fetchCalendarData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        loading = false;
        return;
      }

      const res = await fetch('http://localhost:8000/api/calendar/', {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        calendarData = await res.json();
      }
    } catch (error) {
      console.error('Failed to fetch calendar data:', error);
    } finally {
      loading = false;
    }
  };

  // Get quiz count for a specific date
  const getQuizCount = (date) => {
    const dateStr = formatDate(date);
    return calendarData[dateStr] || 0;
  };

  // Format date to YYYY-MM-DD
  const formatDate = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Get days in month
  const getDaysInMonth = (year, month) => {
    return new Date(year, month + 1, 0).getDate();
  };

  // Get first day of month (0 = Sunday, 6 = Saturday)
  const getFirstDayOfMonth = (year, month) => {
    return new Date(year, month, 1).getDay();
  };

  // Generate calendar days
  $: calendarDays = (() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);
    
    const days = [];
    
    // Previous month's days
    const prevMonth = month === 0 ? 11 : month - 1;
    const prevYear = month === 0 ? year - 1 : year;
    const daysInPrevMonth = getDaysInMonth(prevYear, prevMonth);
    
    for (let i = firstDay - 1; i >= 0; i--) {
      const date = new Date(prevYear, prevMonth, daysInPrevMonth - i);
      days.push({ date, isCurrentMonth: false });
    }
    
    // Current month's days
    for (let i = 1; i <= daysInMonth; i++) {
      const date = new Date(year, month, i);
      days.push({ date, isCurrentMonth: true });
    }
    
    // Next month's days to fill the grid
    const remainingDays = 42 - days.length; // 6 rows * 7 days
    const nextMonth = month === 11 ? 0 : month + 1;
    const nextYear = month === 11 ? year + 1 : year;
    
    for (let i = 1; i <= remainingDays; i++) {
      const date = new Date(nextYear, nextMonth, i);
      days.push({ date, isCurrentMonth: false });
    }
    
    return days;
  })();

  const previousMonth = () => {
    currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1);
  };

  const nextMonth = () => {
    currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1);
  };

  const selectDate = (date) => {
    selectedDate = date;
  };

  const handleKeyDown = (event, date) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      selectDate(date);
    }
  };

  const getActivityClass = (count) => {
    if (count === 0) return 'no-activity';
    if (count <= 2) return 'low-activity';
    if (count <= 5) return 'medium-activity';
    return 'high-activity';
  };

  $: currentMonth = currentDate.getMonth();
  $: currentYear = currentDate.getFullYear();

</script>

<div class="calendar-wrapper">
  <h3>Quiz Activity Calendar</h3>
  {#if loading}
    <p class="loading">Loading calendar...</p>
  {:else}
    <div class="calendar-container">
      <div class="calendar-header">
        <button class="nav-btn" on:click={previousMonth}>‹</button>
        <h4>{monthNames[currentMonth]} {currentYear}</h4>
        <button class="nav-btn" on:click={nextMonth}>›</button>
      </div>
      
      <div class="calendar-grid">
        {#each dayNames as dayName}
          <div class="day-name">{dayName}</div>
        {/each}
        
        {#each calendarDays as { date, isCurrentMonth }}
          {@const count = getQuizCount(date)}
          {@const activityClass = getActivityClass(count)}
          <div 
            class="calendar-day {activityClass}"
            class:not-current-month={!isCurrentMonth}
            class:selected={selectedDate && formatDate(selectedDate) === formatDate(date)}
            on:click={() => selectDate(date)}
            on:keydown={(e) => handleKeyDown(e, date)}
            role="button"
            tabindex="0"
          >
            <span class="day-number">{date.getDate()}</span>
            {#if count > 0}
              <span class="activity-badge">{count}</span>
            {/if}
          </div>
        {/each}
      </div>
    </div>

    {#if selectedDate}
      {@const count = getQuizCount(selectedDate)}
      <div class="selected-info">
        <p>
          <strong>{selectedDate.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</strong>
        </p>
        <p>
          {count > 0 ? `${count} quiz${count === 1 ? '' : 'es'} taken` : 'No quizzes taken'}
        </p>
      </div>
    {/if}

    <div class="legend">
      <span class="legend-item">
        <span class="legend-box no-activity"></span>
        No activity
      </span>
      <span class="legend-item">
        <span class="legend-box low-activity"></span>
        1-2 quizzes
      </span>
      <span class="legend-item">
        <span class="legend-box medium-activity"></span>
        3-5 quizzes
      </span>
      <span class="legend-item">
        <span class="legend-box high-activity"></span>
        6+ quizzes
      </span>
    </div>
  {/if}
</div>

<style>
  .calendar-wrapper {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    margin-top: 24px;
  }

  h3 {
    margin: 0 0 20px 0;
    color: #333;
    font-size: 1.4rem;
    font-weight: 600;
  }

  .loading {
    text-align: center;
    color: #666;
    padding: 20px;
  }

  .calendar-container {
    margin-bottom: 20px;
  }

  .calendar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .calendar-header h4 {
    margin: 0;
    font-size: 1.2rem;
    color: #333;
  }

  .nav-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #68318d;
    padding: 5px 15px;
    border-radius: 4px;
    transition: background-color 0.2s;
  }

  .nav-btn:hover {
    background-color: #f0f0f0;
  }

  .calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 4px;
  }

  .day-name {
    text-align: center;
    font-weight: 600;
    color: #666;
    padding: 10px;
    font-size: 0.85rem;
  }

  .calendar-day {
    position: relative;
    padding: 8px;
    border-radius: 8px;
    transition: all 0.2s ease;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60px;
    background: white;
    border: 1px solid #e0e0e0;
  }

  .calendar-day:hover {
    background-color: #f0f0f0;
    transform: scale(1.05);
  }

  .calendar-day.selected {
    border: 2px solid #68318d;
    box-shadow: 0 0 0 2px rgba(104, 49, 141, 0.2);
  }

  .calendar-day.low-activity {
    background: linear-gradient(135deg, #f0e5ff 0%, #e8d5ff 100%);
    border-color: #e8d5ff;
  }

  .calendar-day.medium-activity {
    background: linear-gradient(135deg, #e8d5ff 0%, #d4b3ff 100%);
    border-color: #d4b3ff;
  }

  .calendar-day.high-activity {
    background: linear-gradient(135deg, #d4b3ff 0%, #b290f5 100%);
    border-color: #b290f5;
  }

  .calendar-day.not-current-month {
    opacity: 0.3;
  }

  .day-number {
    font-size: 0.95rem;
    font-weight: 500;
  }

  .activity-badge {
    background: #68318d;
    color: white;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: bold;
    margin-top: 4px;
  }

  .selected-info {
    background: #f8f9fa;
    padding: 16px;
    border-radius: 8px;
    margin-top: 16px;
    border-left: 4px solid #b290f5;
  }

  .selected-info p {
    margin: 4px 0;
    color: #333;
  }

  .selected-info p:first-child {
    font-size: 1.05rem;
  }

  .legend {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid #e0e0e0;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    color: #666;
  }

  .legend-box {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 1px solid #ddd;
  }

  .legend-box.no-activity {
    background: white;
  }

  .legend-box.low-activity {
    background: linear-gradient(135deg, #f0e5ff 0%, #e8d5ff 100%);
  }

  .legend-box.medium-activity {
    background: linear-gradient(135deg, #e8d5ff 0%, #d4b3ff 100%);
  }

  .legend-box.high-activity {
    background: linear-gradient(135deg, #d4b3ff 0%, #b290f5 100%);
  }
</style>
