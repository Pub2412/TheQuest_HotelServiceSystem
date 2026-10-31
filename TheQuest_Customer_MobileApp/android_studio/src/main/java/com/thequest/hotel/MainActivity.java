package com.thequest.hotel;

import android.app.Activity;
import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;

public class MainActivity extends Activity {
    private static final String EMULATOR_URL = "http://10.0.2.2:5000/";
    private static final String USB_URL = "http://127.0.0.1:5000/";

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        WebView webView = new WebView(this);
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M
                        && checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                        != PackageManager.PERMISSION_GRANTED) {
                    requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, 1001);
                    return;
                }
                for (String resource : request.getResources()) {
                    if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource)) {
                        runOnUiThread(() -> request.grant(new String[]{resource}));
                        return;
                    }
                }
            }
        });
        webView.setWebViewClient(new WebViewClient() {
            private boolean triedUsb;

            @Override
            public void onReceivedError(WebView view, int errorCode, String description,
                                        String failingUrl) {
                if (!triedUsb && failingUrl.startsWith(EMULATOR_URL)) {
                    triedUsb = true;
                    view.loadUrl(USB_URL);
                }
            }
        });
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M
                && checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, 1001);
        }
        webView.loadUrl(EMULATOR_URL);
        setContentView(webView);
    }
}
