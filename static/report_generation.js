document.addEventListener('DOMContentLoaded', function() {
    const searchQuery = document.getElementById('search_query');
    const searchResults = document.getElementById('search_results');
    const reportForm = document.getElementById('report-form');
    const prevPageButton = document.getElementById('prev_page');
    const nextPageButton = document.getElementById('next_page');
    const pageNumber = document.getElementById('page_number');
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

    let dobValue = '';
    function fetchPatientData(keys, page) {
        fetch(`${loadPatientInfoUrl}?keys=${keys.join('&keys=')}&page=${page}`)
            .then(response => response.json())
            .then(data => {
                if (data.patient_data.length > 0) {
                    const patient = data.patient_data[0];
                    document.getElementById('db_key').value = patient.db_key;
                    document.getElementById('patient_name').value = patient.name || '';
                    dobValue = patient.dob || '';
                    document.getElementById('scan_date').value = patient.scan_date || '';
                    document.getElementById('scan_type').value = '';
                    document.getElementById('scan_area').value = '';
                    document.getElementById('scan_details').value = '';
                    document.getElementById('tumor_details').value = '';
                    document.getElementById('tumor_class').value = '0';
                    document.getElementById('diagnosis_opinion').value = '';
                    document.getElementById('treatment_plan').value = '';

                    const segmentationImage = document.getElementById('segmentation_image');
                    segmentationImage.innerHTML = '';
                    if (patient.image_url) {
                        const img = document.createElement('img');
                        img.src = patient.image_url;
                        img.className = 'img-fluid';
                        segmentationImage.appendChild(img);
                    }

                    reportForm.style.display = 'block';
                    totalPages = Math.ceil(data.total / data.per_page);
                    pageNumber.textContent = `Page ${page} of ${totalPages}`;
                    document.getElementById('pagination').style.display = totalPages > 1 ? 'block' : 'none';
                } else {
                    reportForm.style.display = 'none';
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

    window.generatePDF = function() {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        // 맑은 고딕 폰트 설정
        doc.setFont('malgunbd');

        doc.text('환자 정보', 10, 10);
        doc.text('이름: ' + document.getElementById('patient_name').value, 10, 20);
        doc.text('스캔 날짜: ' + document.getElementById('scan_date').value, 10, 30);

        doc.text('스캔 정보 및 결과', 10, 40);
        doc.text('스캔 유형: ' + document.getElementById('scan_type').value, 10, 50);
        doc.text('스캔 부위: ' + document.getElementById('scan_area').value, 10, 60);
        doc.text('스캔 기술적 세부사항: ' + document.getElementById('scan_details').value, 10, 70);

        doc.text('세그멘테이션 결과', 10, 80);
        const img = document.querySelector('#segmentation_image img');
        if (img) {
            doc.text('이미지 URL: ' + img.src, 10, 90);
        }
        doc.text('종양의 위치 및 크기: ' + document.getElementById('tumor_details').value, 10, 100);
        doc.text('종양 클래스: ' + document.getElementById('tumor_class').value, 10, 110);

        doc.text('진단 및 소견', 10, 120);
        doc.text(document.getElementById('diagnosis_opinion').value, 10, 130);

        doc.text('치료 계획 및 권고 사항', 10, 140);
        doc.text(document.getElementById('treatment_plan').value, 10, 150);

        const patientName = document.getElementById('patient_name').value;
        const fileName = `${patientName}${dobValue}.pdf`;

        doc.save(fileName);
    }
});
