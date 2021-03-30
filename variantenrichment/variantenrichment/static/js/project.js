/* Project specific Javascript goes here. */
document.addEventListener('DOMContentLoaded', () => {
   const genesFile = document.querySelector('.detail--genes').dataset.file;
   const genesValue = document.querySelector('.detail__value');
   const genesArr = genesFile.split('/');
   genesValue.innerText = genesArr[genesArr.length - 1];
});
