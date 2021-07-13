/* Project specific Javascript goes here. */
document.addEventListener('DOMContentLoaded', () => {
   initFileNames();
   initResultTable();
   initPopulationFields();
});

function initPopulationFields() {
   const populationField = document.getElementById('id_population');
   if (!populationField) return;

   const checkboxes = [].slice.call(document.querySelectorAll('input[type=checkbox][name="population"]'));
   const checkboxAll = document.querySelector('.do-checkAll');
   let populationArr = []

   checkboxes.forEach(checkbox => {
      checkbox.addEventListener('change', () => {
         if (checkbox === checkboxAll) {
            populationArr = [];

            checkboxes.forEach(checkboxPart => {
               if (checkboxPart.classList.contains('do-checkAll')) return;

               checkboxPart.checked = checkbox.checked;
            });
         } else {
            populationArr = checkboxes
             .filter(i => i.checked && i.value)
             .map(i => i.value);

            if (populationArr.length === 5) {
               populationArr = [];
               checkboxAll.checked = true
            } else {
               checkboxAll.checked = false
            }
         }

         populationField.value = populationArr.join(",")
      })
   });
}

function initFileNames() {
   const detailsWithFiles = [].slice.call(document.querySelectorAll('.project-detail[data-file]'));

   detailsWithFiles.forEach(detail => {
      let nameSplit = detail.dataset.file.split('/');
      const detailValue = detail.querySelector('.project-detail__value');
      detailValue.innerText = nameSplit[nameSplit.length - 1]
   });
}

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
