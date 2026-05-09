// Chart.js initialization and configuration
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts on the page that declare data attributes
    const chartCanvases = document.querySelectorAll('canvas[data-chart]');
    
    chartCanvases.forEach(canvas => {
        try {
            const chartType = canvas.getAttribute('data-chart-type') || 'bar';
            const chartData = JSON.parse(canvas.getAttribute('data-chart-data') || '{}');
            initChart(canvas, chartType, chartData);
        } catch (err) {
            console.warn('Could not initialize chart for canvas', canvas, err);
        }
    });
});

function initChart(canvas, type, data) {
    const ctx = canvas.getContext('2d');
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                mode: 'index',
                intersect: false,
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return value + '%';
                    }
                }
            }
        }
    };
    
    // Merge custom options safely
    const options = Object.assign({}, defaultOptions, (data.options || {}));
    
    new Chart(ctx, {
        type: type,
        data: data,
        options: options
    });
}

// Utility function to create progress chart
function createProgressChart(canvasId, dates, scores) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    const data = {
        labels: dates,
        datasets: [{
            label: 'Average Score',
            data: scores,
            borderColor: '#10B981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            fill: true,
            tension: 0.4
        }]
    };
    
    const options = {
        responsive: true,
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
        }
    };
    
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: options
    });
}

// Utility function to create topic performance chart
function createTopicPerformanceChart(canvasId, topics, scores) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    const backgroundColors = scores.map(score => 
        score >= 70 ? '#10B981' : '#EF4444'
    );
    
    const data = {
        labels: topics,
        datasets: [{
            label: 'Average Score (%)',
            data: scores,
            backgroundColor: backgroundColors,
            borderWidth: 1
        }]
    };
    
    const options = {
        responsive: true,
        indexAxis: 'y',
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                beginAtZero: true,
                max: 100,
                ticks: {
                    callback: function(value) {
                        return value + '%';
                    }
                }
            }
        }
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: data,
        options: options
    });
}

// This file is no longer needed as the chart initialization
// has been moved directly to the analytics.html template
// You can keep this file for other chart-related functions if needed

// Function to format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
    });
}

// Function to handle chart responsiveness on window resize
function handleChartResize() {
    if (typeof performanceChart !== 'undefined') {
        performanceChart.resize();
    }
}

// Add event listener for window resize
window.addEventListener('resize', handleChartResize);