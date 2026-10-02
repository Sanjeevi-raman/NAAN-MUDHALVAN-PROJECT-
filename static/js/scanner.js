/**
 * PocketSmart AI - Camera & Product Scanner Client
 * Interacts with navigator.mediaDevices.getUserMedia for live camera feed,
 * supports mobile environment-facing camera, image capture to canvas,
 * and standard file upload fallback.
 */

let videoStream = null;

function initScanner(videoElemId, startBtnId, captureBtnId, stopBtnId, fileInputId, previewImgId) {
    const video = document.getElementById(videoElemId);
    const startBtn = document.getElementById(startBtnId);
    const captureBtn = document.getElementById(captureBtnId);
    const stopBtn = document.getElementById(stopBtnId);
    const fileInput = document.getElementById(fileInputId);
    const previewImg = document.getElementById(previewImgId);

    if (!video || !startBtn) return;

    // 1. Start Camera
    startBtn.addEventListener('click', async () => {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                alert("Direct camera access is not supported by your browser or environment. Please use the file upload option below.");
                return;
            }

            const constraints = {
                video: {
                    facingMode: { ideal: "environment" },
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            };

            videoStream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = videoStream;
            video.style.display = "block";
            if (previewImg) previewImg.style.display = "none";

            startBtn.style.display = "none";
            if (captureBtn) captureBtn.style.display = "inline-flex";
            if (stopBtn) stopBtn.style.display = "inline-flex";
        } catch (err) {
            console.error("Camera access error:", err);
            alert("Could not access camera (Permission denied or hardware unavailable). Please use the image upload option.");
        }
    });

    // 2. Capture Snapshot
    if (captureBtn) {
        captureBtn.addEventListener('click', () => {
            if (!videoStream) return;

            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            canvas.toBlob((blob) => {
                if (!blob) return;

                // Create a File from Blob and attach to file input
                const file = new File([blob], `scan_capture_${Date.now()}.jpg`, { type: 'image/jpeg' });
                const container = new DataTransfer();
                container.items.add(file);
                fileInput.files = container.files;

                // Show preview
                if (previewImg) {
                    previewImg.src = URL.createObjectURL(blob);
                    previewImg.style.display = "block";
                    video.style.display = "none";
                }

                // Stop camera stream
                stopCameraStream();
            }, 'image/jpeg', 0.92);
        });
    }

    // 3. Stop Camera
    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            stopCameraStream();
        });
    }

    // 4. File input change preview
    if (fileInput && previewImg) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                previewImg.src = URL.createObjectURL(file);
                previewImg.style.display = "block";
                video.style.display = "none";
                stopCameraStream();
            }
        });
    }

    function stopCameraStream() {
        if (videoStream) {
            videoStream.getTracks().forEach(track => track.stop());
            videoStream = null;
        }
        startBtn.style.display = "inline-flex";
        if (captureBtn) captureBtn.style.display = "none";
        if (stopBtn) stopBtn.style.display = "none";
    }
}
