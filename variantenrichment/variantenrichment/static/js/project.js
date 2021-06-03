/* Project specific Javascript goes here. */
document.addEventListener('DOMContentLoaded', () => {
   const detailsWithFiles = [].slice.call(document.querySelectorAll('.detail[data-file]'));

   detailsWithFiles.forEach(detail => {
      let nameSplit = detail.dataset.file.split('/');
      const detailValue = detail.querySelector('.detail__value');
      detailValue.innerText = nameSplit[nameSplit.length - 1]
   })
});

