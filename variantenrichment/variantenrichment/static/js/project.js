/* Project specific Javascript goes here. */
document.addEventListener('DOMContentLoaded', () => {
   initFileNames();
   initResultTable();
});

function initFileNames() {
   const detailsWithFiles = [].slice.call(document.querySelectorAll('.project-detail[data-file]'));

   detailsWithFiles.forEach(detail => {
      let nameSplit = detail.dataset.file.split('/');
      const detailValue = detail.querySelector('.project-detail__value');
      detailValue.innerText = nameSplit[nameSplit.length - 1]
   });
}

function initResultTable() {
   const resultTable = document.querySelector(".results-table");
   if (!resultTable) return;

   const shortViewButton = document.querySelector(".do-displayCompact");

   shortViewButton.addEventListener("click", () => {
      if (shortViewButton.classList.contains("is-active")) {
         shortViewButton.classList.remove("is-active");
         resultTable.classList.remove("results-table__compact");
      } else {
         shortViewButton.classList.add("is-active");
         resultTable.classList.add("results-table__compact");
      }
   })

   const pValueInput = document.querySelector(".do-displayRelevant");
   const tableRows = [].slice.call(document.querySelectorAll(".results-table tbody tr"));

   pValueInput.addEventListener("keyup", () => {
      const pVal = parseFloat(pValueInput.value) || 1;

      tableRows.forEach(tr => {
         tr.classList.remove("is-hidden");

         const pValCell = tr.querySelector(".results-table__p");
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
