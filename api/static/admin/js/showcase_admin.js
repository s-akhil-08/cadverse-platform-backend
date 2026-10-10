// (function($) {
//     $(document).ready(function() {
//         // Auto-fetch title on feedback change
//         $('#id_feedback').change(function() {
//             var feedbackId = $(this).val();
//             if (feedbackId) {
//                 $.ajax({
//                     url: '/api/get-project-title/' + feedbackId + '/',  // New endpoint you'll add
//                     success: function(data) {
//                         $('#id_title').val(data.title);
//                     }
//                 });
//             }
//         });

//         // Region selection for non-square files
//         function initCrop(inputId) {
//             var input = $('#' + inputId)[0];
//             input.addEventListener('change', function(e) {
//                 var file = e.target.files[0];
//                 if (file) {
//                     var reader = new FileReader();
//                     reader.onload = function(event) {
//                         var media = file.type.startsWith('video') ? document.createElement('video') : new Image();
//                         media.src = event.target.result;
//                         media.onload = function() {
//                             var width = media.videoWidth || media.width;
//                             var height = media.videoHeight || media.height;
//                             if (width !== height) {  // Not 1:1
//                                 alert('Select square region (1:1) for frontend display.');
//                                 // Simple crop logic: Use library like Cropper.js (add via CDN if needed)
//                                 // For demo: Prompt for coords
//                                 var x = prompt('Enter crop X (0-' + width + '):', '0');
//                                 var y = prompt('Enter crop Y (0-' + height + '):', '0');
//                                 $('#id_crop_data').val(JSON.stringify({x: x, y: y, width: Math.min(width, height), height: Math.min(width, height)}));
//                             }
//                         };
//                     };
//                     reader.readAsDataURL(file);
//                 }
//             });
//         }
//         initCrop('id_before_file');
//         initCrop('id_after_file');
//     });
// })(django.jQuery);



// (function($) {
//     $(document).ready(function() {
//         const titleField = $('#id_title');
//         const feedbackField = $('#id_feedback');

//         feedbackField.change(function() {
//             const feedbackId = $(this).val();
//             if (!feedbackId) {
//                 titleField.val('');
//                 return;
//             }

//             // Call our API to get project title
//             fetch(`/api/get-project-title/${feedbackId}/`)
//                 .then(response => response.json())
//                 .then(data => {
//                     if (data.title) {
//                         titleField.val(data.title);
//                     }
//                 })
//                 .catch(() => console.log("Title fetch failed (normal if API not ready yet)"));
//         });
//     });
// })(django.jQuery);




(function($) {
    $(document).ready(function() {
        const titleField = $('#id_title');
        const feedbackField = $('#id_feedback');

        feedbackField.change(function() {
            const feedbackId = $(this).val();
            if (!feedbackId) {
                titleField.val('');
                return;
            }

            // Call our API to get project title
            fetch(`/api/get-project-title/${feedbackId}/`)
                .then(response => response.json())
                .then(data => {
                    if (data.title) {
                        titleField.val(data.title);
                    }
                })
                .catch(() => console.log("Title fetch failed (normal if API not ready yet)"));
        });
    });
})(django.jQuery);