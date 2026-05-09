// Dashboard-specific chart initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize performance chart if it exists on the page
    const performanceChartCanvas = document.getElementById('performanceChart');
    
    if (performanceChartCanvas) {
        initPerformanceChart();
    }
    
    // Animate progress bars
    const progressBars = document.querySelectorAll('.score-meter');
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = width;
            bar.style.transition = 'width 1s ease-in-out';
        }, 100);
    });
});

function initPerformanceChart() {
    const ctx = document.getElementById('performanceChart').getContext('2d');
    
    // Parse the JSON data passed from Flask
    const dailyLabels = JSON.parse(document.getElementById('dailyLabels').textContent);
    const dailyScores = JSON.parse(document.getElementById('dailyScores').textContent);
    const dailyAverages = JSON.parse(document.getElementById('dailyAverages').textContent);
    
    // Replace null values with a special value that Chart.js can handle
    const processedScores = dailyScores.map(score => score === null ? NaN : score);
    const processedAverages = dailyAverages.map(avg => avg === null ? NaN : avg);
    
    const performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dailyLabels,
            datasets: [
                // Dataset 1: Quiz Score (Solid Green Line)
                {
                    label: 'Daily Score (%)',
                    data: processedScores,
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.05)',
                    tension: 0.3,
                    fill: false,
                    spanGaps: true,
                    pointBackgroundColor: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return isNaN(value) ? 'transparent' : 'rgb(34, 197, 94)';
                    },
                    pointBorderColor: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return isNaN(value) ? 'transparent' : '#fff';
                    },
                    pointHoverBackgroundColor: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return isNaN(value) ? 'transparent' : '#fff';
                    },
                    pointHoverBorderColor: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return isNaN(value) ? 'transparent' : 'rgb(34, 197, 94)';
                    },
                    pointRadius: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return isNaN(value) ? 0 : 3;
                    },
                    pointHoverRadius: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return isNaN(value) ? 0 : 5;
                    },
                    borderWidth: 2,
                },
                // Dataset 2: Average Score (Dashed Yellow Line)
                {
                    label: 'Running Average (%)',
                    data: processedAverages,
                    borderColor: 'rgb(234, 179, 8)',
                    backgroundColor: 'rgba(234, 179, 8, 0.05)',
                    borderDash: [6, 4],
                    tension: 0.3,
                    fill: false,
                    spanGaps: true,
                    pointBackgroundColor: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return isNaN(value) ? 'transparent' : 'rgb(234, 179, 8)';
                    },
                    pointBorderColor: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return isNaN(value) ? 'transparent' : '#fff';
                    },
                    pointHoverBackgroundColor: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return isNaN(value) ? 'transparent' : '#fff';
                    },
                    pointHoverBorderColor: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return isNaN(value) ? 'transparent' : 'rgb(234, 179, 8)';
                    },
                    pointRadius: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return isNaN(value) ? 0 : 3;
                    },
                    pointHoverRadius: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return isNaN(value) ? 0 : 5;
                    },
                    borderWidth: 2,
                }
            ]
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
                    },
                    title: {
                        display: true,
                        text: 'Score (%)',
                        font: {
                            weight: 'bold'
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date (MM/DD)',
                        font: {
                            weight: 'bold',
                            style: 'normal'
                        }
                    },
                    ticks: {
                        font: {
                            style: 'normal'
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y + '%';
                            }
                            return label;
                        }
                    }
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            weight: 'bold'
                        }
                    }
                }
            }
        }
    });
    
    return performanceChart;
}

// Function to handle chart responsiveness on window resize
function handleChartResize() {
    if (typeof performanceChart !== 'undefined') {
        performanceChart.resize();
    }
}

// Add event listener for window resize
window.addEventListener('resize', handleChartResize);