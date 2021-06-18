/* Project specific Javascript goes here. */
document.addEventListener('DOMContentLoaded', () => {
   initResultTable();

   const detailsWithFiles = [].slice.call(document.querySelectorAll('.detail[data-file]'));

   detailsWithFiles.forEach(detail => {
      let nameSplit = detail.dataset.file.split('/');
      const detailValue = detail.querySelector('.detail__value');
      detailValue.innerText = nameSplit[nameSplit.length - 1]
   });
});

function initResultTable() {
   const resultTable = document.querySelector(".table-results");
   if (!resultTable) return;

   const shortViewButton = document.querySelector(".do-displayCompact");

   shortViewButton.addEventListener("click", () => {
      if (shortViewButton.classList.contains("is-active")) {
         shortViewButton.classList.remove("is-active");
         resultTable.classList.remove("table-results__compact");
      } else {
         shortViewButton.classList.add("is-active");
         resultTable.classList.add("table-results__compact");
      }
   })

   const pValueInput = document.querySelector(".do-displayRelevant");
   const tableRows = [].slice.call(document.querySelectorAll(".table-results tbody tr"));

   pValueInput.addEventListener("keyup", () => {
      const pVal = parseFloat(pValueInput.value) || 1;

      tableRows.forEach(tr => {
         tr.classList.remove("is-hidden");

         const pValCell = tr.querySelector(".table-results__p");
         if (!pValCell) {
            if (tr.previousElementSibling.classList.contains("is-hidden")){
               tr.classList.add("is-hidden");
            }
            return;
         }

         if (parseFloat(pValCell.innerText) <= pVal) return;

         tr.classList.add("is-hidden");
      });
   });
}
