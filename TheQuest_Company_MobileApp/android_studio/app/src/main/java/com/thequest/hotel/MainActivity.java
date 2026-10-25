package com.thequest.hotel;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    private static final String EMULATOR_URL = "http://10.0.2.2:5000/";
    private static final String USB_URL = "http://127.0.0.1:5000/";

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        WebView webView = new WebView(this);
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
        settings.setJavaScriptEnabled(false);
        settings.setDomStorageEnabled(true);
        webView.loadUrl(EMULATOR_URL);
        setContentView(webView);
    }
}
