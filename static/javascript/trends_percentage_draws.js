

console.log("Funciona el script de graficos ")
      
//       // GRAFICO DE PRESLOPE LIMIT Y OBJECTIVE ORDENADO
// const preslopesLimit = dataFetch.Limit
//    .map(d => d.PreSlope)
//    .filter(val => val !== null && !isNaN(val))
//    .sort((a, b) => a - b);

// const preslopesObjective = dataFetch.Objective
//    .map(d => d.PreSlope)
//    .filter(val => val !== null && !isNaN(val))
//    .sort((a, b) => a - b);

// // Estadísticas
// const meanLimit = dataFetch.StatsPreSlope.Limit.mean;
// const stdLimit = dataFetch.StatsPreSlope.Limit.std;
// const meanObj = dataFetch.StatsPreSlope.Objective.mean;
// const stdObj = dataFetch.StatsPreSlope.Objective.std;

// // Eje X común
// const longestLength = Math.max(preslopesLimit.length, preslopesObjective.length);
// const xLabels = Array.from({ length: longestLength }, (_, i) => i + 1);

// const ctx = document.getElementById('chartPreslope').getContext('2d');
// new Chart(ctx, {
//    type: 'line',
//    data: {
//       labels: xLabels,
//       datasets: [
//          {
//             label: 'Limit PreSlope (sorted)',
//             data: preslopesLimit,
//             borderWidth: 1,
//             borderColor: '#e74c3c',
//             backgroundColor: '#e74c3c',
//             pointRadius: 0,
//             fill: false,
//             tension: 0.1
//          },
//          {
//             label: 'Objective PreSlope (sorted)',
//             data: preslopesObjective,
//             borderWidth: 1,
//             borderColor: 'green',
//             backgroundColor: 'rgba(0,255,0,0.1)',
//             pointRadius: 0,
//             fill: false,
//             tension: 0.1
//          },
//          // Líneas horizontales estadísticas Limit
//          {
//             label: 'Mean Limit',
//             data: Array(xLabels.length).fill(meanLimit),
//             borderColor: '#7b241c',
//             borderDash: [5, 5],
//             borderWidth: 1,
//             pointRadius: 0,
//             fill: false
//          },
//          {
//             label: '+1 STD Limit',
//             data: Array(xLabels.length).fill(meanLimit + stdLimit),
//             borderColor: '#dc7633',
//             borderDash: [5, 5],
//             borderWidth: 1,
//             pointRadius: 0,
//             fill: false
//          },
//          {
//             label: '-1 STD Limit',
//             data: Array(xLabels.length).fill(meanLimit - stdLimit),
//             borderColor: '#dc7633',
//             borderDash: [5, 5],
//             borderWidth: 1,
//             pointRadius: 0,
//             fill: false
//          },
//          // Líneas horizontales estadísticas Objective
//          {
//             label: 'Mean Objective',
//             data: Array(xLabels.length).fill(meanObj),
//             borderColor: '#2980b9',
//             borderDash: [5, 5],
//             borderWidth: 1,
//             pointRadius: 0,
//             fill: false
//          },
//          {
//             label: '+1 STD Objective',
//             data: Array(xLabels.length).fill(meanObj + stdObj),
//             borderColor: '#34495e',
//             borderDash: [5, 5],
//             borderWidth: 1,
//             pointRadius: 0,
//             fill: false
//          },
//          {
//             label: '-1 STD Objective',
//             data: Array(xLabels.length).fill(meanObj - stdObj),
//             borderColor: '#34495e',
//             borderDash: [5, 5],
//             borderWidth: 1,
//             pointRadius: 0,
//             fill: false
//          }
//       ]
//    },
//    options: {
//       responsive: true,
//       scales: {
//          x: {
//             title: { display: true, text: 'Index (sorted)' }
//          },
//          y: {
//             title: { display: true, text: 'PreSlope' }
//          }
//       }
//    }
// });
