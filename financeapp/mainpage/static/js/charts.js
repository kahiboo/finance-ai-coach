// Only run this if the chart element exists on the page
const ctx = document.getElementById('spendingChart');

if (ctx) {
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
      datasets: [{
        label: 'Spending ($)',
        data: [420, 350, 610, 280], // Example data, replace with real data later
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79,70,229,0.1)',
        borderWidth: 2,
        tension: 0.3,
        fill: true,
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true }
      },
      plugins: {
        legend: {
          display: false
        }
      }
    }
  });
}

