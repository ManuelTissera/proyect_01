
const getDataToDraw = async () => {
   const url = '/api/macd_data';

   const dataFetch = await fetch(url).then(res => res.json()).then(res => res).catch(err => console.error(err));
   
   
   let label = 'Positive Higher';
   
   // const ctx = document.getElementById('chartDrawRSI').getContext('2d');
   // new Chart(ctx, {
   //    type: 'circle',
   //    data: {
   //       labels: xLabels,
   //       datasets: [
   //          label: `RSI ${label}`,
   //          data
   //       ]
   //    }
   // })
}