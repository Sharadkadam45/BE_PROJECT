function previewImage(input) {
    if (!input.files || !input.files[0]) {
        return;
    }

    const reader = new FileReader();
    reader.onload = function () {
        const preview = document.getElementById('preview');
        if (preview) {
            preview.src = reader.result;
            preview.style.display = 'block';
        }
    };
    reader.readAsDataURL(input.files[0]);
}

function showLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.display = 'block';
    }
}

function toggleFAQ(element) {
    const item = element.parentElement;
    if (!item) {
        return;
    }

    const allItems = document.querySelectorAll('.faq-item');
    allItems.forEach(faq => {
        if (faq !== item) {
            faq.classList.remove('active');
        }
    });

    item.classList.toggle('active');
}
