// app/static/js/chart-init.js - NO OVERLAY VERSION
console.log('Chart Init JS loaded - initializing charts');

// Global chart instance
let performanceChart = null;

// Initialize chart when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, checking for performance chart...');
    
    const chartCanvas = document.getElementById('performanceChart');
    if (!chartCanvas) {
        console.log('Performance chart canvas not found');
        return;
    }
    
    // Get chart data from global variables
    let chartData = window.chartData || null;
    
    console.log('Chart data from window.chartData:', chartData);
    
    // Initialize the chart
    initPerformanceChart(chartData);
});

function initPerformanceChart(data) {
    const ctx = document.getElementById('performanceChart');
    if (!ctx) {
        console.error('Performance chart canvas not found!');
        return;
    }
    
    console.log('initPerformanceChart called with data:', data);
    
    // Default empty data
    const defaultLabels = ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'];
    let labels = defaultLabels;
    let averages = [0, 0, 0, 0, 0, 0, 0];
    
    // Use provided data if available
    if (data && data.labels && Array.isArray(data.labels)) {
        labels = data.labels;
        console.log('Using labels from data:', labels);
    }
    if (data && data.averages && Array.isArray(data.averages)) {
        // Convert null values to 0
        averages = data.averages.map(avg => (avg === null || avg === undefined) ? 0 : avg);
        console.log('Using averages from data (nulls converted to 0):', averages);
    }
    
    // Destroy existing chart if it exists
    if (performanceChart) {
        performanceChart.destroy();
    }
    
    // REMOVE ANY EXISTING OVERLAY IMMEDIATELY
    const container = ctx.parentElement;
    const existingOverlays = container.querySelectorAll('.chart-message, .no-data-overlay, [class*="overlay"]');
    existingOverlays.forEach(overlay => overlay.remove());
    
    // Create chart configuration - ALWAYS show solid line, NO overlay
    const config = {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Your Performance Score',
                data: averages,
                borderColor: '#10B981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#10B981',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Score (%)',
                        font: { size: 12 }
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        },
                        stepSize: 20
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date',
                        font: { size: 12 }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 10
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Score: ${context.raw}%`;
                        }
                    }
                }
            }
        }
    };
    
    // Create the chart
    performanceChart = new Chart(ctx, config);
    console.log('Performance chart created successfully with data:', {labels, averages});
    
    // DOUBLE CHECK: Remove any overlay that might have been added after chart creation
    setTimeout(() => {
        const allOverlays = document.querySelectorAll('.chart-message, .no-data-overlay, [class*="message"]');
        allOverlays.forEach(overlay => {
            if (overlay.innerHTML && (overlay.innerHTML.includes('No Data Yet') || overlay.innerHTML.includes('Take a Quiz'))) {
                console.log('Removing stray overlay:', overlay);
                overlay.remove();
            }
        });
    }, 100);
    
    return performanceChart;
}

// Function to update chart with new data
function updatePerformanceChart(labels, averages) {
    console.log('updatePerformanceChart called with:', {labels, averages});
    if (performanceChart) {
        performanceChart.data.labels = labels;
        performanceChart.data.datasets[0].data = averages;
        performanceChart.update();
        console.log('Chart updated with new data');
    } else {
        initPerformanceChart({ labels: labels, averages: averages });
    }
}

// Export for use in other scripts
window.performanceChart = performanceChart;
window.initPerformanceChart = initPerformanceChart;
window.updatePerformanceChart = updatePerformanceChart;