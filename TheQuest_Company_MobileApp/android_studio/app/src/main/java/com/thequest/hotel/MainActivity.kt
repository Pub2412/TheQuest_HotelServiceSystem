package com.thequest.hotel

import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {
    private lateinit var status: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        startPythonBackend()
        setContentView(createLoginView())
    }

    private fun startPythonBackend() {
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
        Python.getInstance().getModule("mobile_backend").callAttr(
            "start_server",
            filesDir.absolutePath
        )
    }

    private fun createLoginView(): LinearLayout {
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 32, 48, 32)
        }
        val title = TextView(this).apply {
            text = "THE QUEST HOTEL"
            textSize = 28f
            gravity = Gravity.CENTER
        }
        val username = EditText(this).apply {
            hint = "Username"
            singleLine = true
        }
        val password = EditText(this).apply {
            hint = "Password"
            inputType = 0x81
            singleLine = true
        }
        val button = Button(this).apply {
            text = "Sign in"
            setOnClickListener {
                authenticate(username.text.toString(), password.text.toString())
            }
        }
        status = TextView(this).apply {
            gravity = Gravity.CENTER
            setPadding(0, 24, 0, 0)
        }
        layout.addView(title, fieldParams())
        layout.addView(username, fieldParams())
        layout.addView(password, fieldParams())
        layout.addView(button, fieldParams())
        layout.addView(status, fieldParams())
        return layout
    }

    private fun fieldParams() = LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT,
        LinearLayout.LayoutParams.WRAP_CONTENT
    ).apply { bottomMargin = 16 }

    private fun authenticate(username: String, password: String) {
        status.text = "Signing in..."
        thread {
            val result = try {
                val connection = URL("http://127.0.0.1:8765/api/login").openConnection() as HttpURLConnection
                connection.requestMethod = "POST"
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json")
                val body = """{"username":"${username.replace("\"", "")}","password":"${password.replace("\"", "")}"}"""
                connection.outputStream.use { it.write(body.toByteArray()) }
                val response = connection.inputStream.bufferedReader().use { it.readText() }
                if (connection.responseCode == 200) "Signed in: $response" else "Invalid credentials"
            } catch (error: Exception) {
                "Backend unavailable: ${error.message}"
            }
            runOnUiThread { status.text = result }
        }
    }
}
