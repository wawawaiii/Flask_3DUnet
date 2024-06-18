document.addEventListener('DOMContentLoaded', function() {
    const searchQuery = document.getElementById('search_query');
    const searchResults = document.getElementById('search_results');
    const patientInfoForm = document.getElementById('patient_info_form');
    const cancelButton = document.getElementById('cancel_button');
    const prevPageButton = document.getElementById('prev_page');
    const nextPageButton = document.getElementById('next_page');
    const pageNumber = document.getElementById('page_number');
    const deleteButton = document.getElementById('delete_button');
    const exportButton = document.getElementById('export_button');
    let currentPage = 1;
    let totalPages = 1;
    let keysCache = [];

    searchQuery.addEventListener('input', function() {
        const query = searchQuery.value.trim();
        if (query.length === 0) {
            searchResults.style.display = 'none';
            return;
        }

        fetch(`${searchPatientUrl}?query=${query}`)
            .then(response => response.json())
            .then(data => {
                searchResults.innerHTML = '';
                if (data.length > 0) {
                    data.forEach(item => {
                        const option = document.createElement('a');
                        option.classList.add('dropdown-item');
                        option.href = '#';
                        option.textContent = item.name_dob.split('_').join(' ');
                        option.addEventListener('click', function() {
                            searchQuery.value = item.name_dob.split('_').join(' ');
                            keysCache = item.keys;
                            currentPage = 1;
                            fetchPatientData(keysCache, currentPage);
                            searchResults.style.display = 'none';
                        });
                        searchResults.appendChild(option);
                    });
                    searchResults.style.display = 'block';
                } else {
                    searchResults.style.display = 'none';
                }
            });
    });

    function fetchPatientData(keys, page) {
        fetch(`${loadPatientInfoUrl}?keys=${keys.join('&keys=')}&page=${page}`)
            .then(response => response.json())
            .then(data => {
                if (data.patient_data.length > 0) {
                    const patient = data.patient_data[0];
                    document.getElementById('db_key').value = patient.db_key;
                    document.getElementById('name').value = patient.name || '';
                    document.getElementById('dob').value = patient.dob || '';
                    document.getElementById('gender').value = patient.gender || 'male';
                    document.getElementById('phone').value = patient.phone || '';
                    document.getElementById('email').value = patient.email || '';
                    document.getElementById('address').value = patient.address || '';
                    document.getElementById('diagnosis').value = patient.diagnosis || '';
                    document.getElementById('medical_history').value = patient.medical_history || '';
                    document.getElementById('treatment_plan').value = patient.treatment_plan || '';
                    document.getElementById('allergies').value = patient.allergies || '';
                    document.getElementById('insurance_info').value = patient.insurance_info || '';
                    document.getElementById('scan_date').value = patient.scan_date || '';
                    document.getElementById('segmentation_result').value = patient.segmentation_result || '';

                    if (patient.image_url) {
                        const imagePreview = document.getElementById('image_preview');
                        imagePreview.innerHTML = `<img src="${patient.image_url}" alt="Segmentation Result" class="img-fluid">`;
                    }

                    patientInfoForm.style.display = 'block';
                    totalPages = Math.ceil(data.total / data.per_page);
                    pageNumber.textContent = `Page ${page} of ${totalPages}`;
                    document.getElementById('pagination').style.display = totalPages > 1 ? 'block' : 'none';
                } else {
                    patientInfoForm.style.display = 'none';
                    document.getElementById('pagination').style.display = 'none';
                }
            });
    }

    prevPageButton.addEventListener('click', function() {
        if (currentPage > 1) {
            currentPage--;
            fetchPatientData(keysCache, currentPage);
        }
    });

    nextPageButton.addEventListener('click', function() {
        if (currentPage < totalPages) {
            currentPage++;
            fetchPatientData(keysCache, currentPage);
        }
    });

    cancelButton.addEventListener('click', function() {
        patientInfoForm.style.display = 'none';
        searchQuery.value = '';
        searchResults.innerHTML = '';
        searchResults.style.display = 'none';
        document.getElementById('pagination').style.display = 'none';
    });

    deleteButton.addEventListener('click', function() {
        const dbKey = document.getElementById('db_key').value;
        if (confirm('정말로 이 환자 정보를 삭제하시겠습니까?')) {
            fetch(`${deletePatientInfoUrl}?db_key=${dbKey}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('환자 정보가 삭제되었습니다.');
                    location.reload(); // 새로고침 추가
                } else {
                    alert('환자 정보 삭제에 실패했습니다.');
                }
            });
        }
    });

    exportButton.addEventListener('click', function() {
        const keys = keysCache.join('&keys=');
        fetch(`${exportPatientInfoUrl}?keys=${keys}`)
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                const name = document.getElementById('name').value;
                const dob = document.getElementById('dob').value;
                const filename = `${name}_${dob}.csv`;
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
            });
    });
});
