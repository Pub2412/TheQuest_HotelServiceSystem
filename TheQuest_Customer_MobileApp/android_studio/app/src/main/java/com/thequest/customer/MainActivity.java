package com.thequest.customer;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;
import android.webkit.RenderProcessGoneDetail;
import android.webkit.WebViewRenderProcess;
import android.webkit.WebViewRenderProcessClient;

public class MainActivity extends Activity {
    private static final String EMULATOR_URL = "http://10.0.2.2:5001/";
    private static final String USB_URL = "http://127.0.0.1:5001/";
    private WebView webView;

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        webView = new WebView(this);
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            private boolean triedUsb;

            @Override
            public void onReceivedError(WebView view, int errorCode, String description,
                                        String failingUrl) {
                if (view.isFocused() && !triedUsb && failingUrl.startsWith(EMULATOR_URL)) {
                    triedUsb = true;
                    view.loadUrl(USB_URL);
                }
            }

            @Override
            public boolean onRenderProcessGone(WebView view, RenderProcessGoneDetail detail) {
                view.destroy();
                webView = new WebView(MainActivity.this);
                configureWebView(webView);
                setContentView(webView);
                webView.loadUrl(EMULATOR_URL);
                return true;
            }
        });
        configureWebView(webView);
        setContentView(webView);
        webView.loadUrl(EMULATOR_URL);
    }

    private void configureWebView(WebView target) {
        WebSettings settings = target.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        target.setWebViewRenderProcessClient(new WebViewRenderProcessClient() {
            @Override
            public void onRenderProcessUnresponsive(WebView view, WebViewRenderProcess renderer) {
                if (renderer != null) {
                    renderer.terminate();
                }
            }

            @Override
            public void onRenderProcessResponsive(WebView view, WebViewRenderProcess renderer) {
                // The renderer recovered; no action is needed.
            }
        });
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
