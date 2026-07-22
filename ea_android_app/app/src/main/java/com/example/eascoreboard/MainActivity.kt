package com.example.eascoreboard

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.webkit.WebChromeClient
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.window.Dialog
import androidx.core.content.ContextCompat
import androidx.work.*
import java.util.concurrent.TimeUnit

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        
        // Schedule background notification updates checker
        scheduleBackgroundPoll()

        setContent {
            EAScoreboardApp()
        }
    }

    private fun scheduleBackgroundPoll() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val workRequest = PeriodicWorkRequestBuilder<SyncNotificationWorker>(15, TimeUnit.MINUTES)
            .setConstraints(constraints)
            .build()

        WorkManager.getInstance(applicationContext).enqueueUniquePeriodicWork(
            "EAScoreboardUpdateCheck",
            ExistingPeriodicWorkPolicy.KEEP,
            workRequest
        )
    }
}

/**
 * JS bridge class exposed as window.AndroidBridge inside the WebView
 */
class AndroidBridge(
    private val context: Context,
    private val onCredentialsChanged: () -> Unit
) {
    private val sharedPref: SharedPreferences = context.getSharedPreferences("EASecurePrefs", Context.MODE_PRIVATE)

    @JavascriptInterface
    fun saveCriticalData(key: String, value: String) {
        sharedPref.edit().putString(key, value).apply()
        // If the web UI changes the WAN URL, credentials or theme, trigger state check
        if (key == "server_wan_url" || key == "ea_login_id" || key == "login_code") {
            onCredentialsChanged()
        }
    }

    @JavascriptInterface
    fun getCriticalData(key: String): String {
        return sharedPref.getString(key, "") ?: ""
    }
}

@SuppressLint("SetJavaScriptEnabled")
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EAScoreboardApp() {
    val context = LocalContext.current
    val sharedPrefs = remember { context.getSharedPreferences("EASecurePrefs", Context.MODE_PRIVATE) }
    
    var showSettings by remember { mutableStateOf(false) }
    var serverWanUrl by remember { mutableStateOf(sharedPrefs.getString("server_wan_url", "") ?: "") }
    var loginId by remember { mutableStateOf(sharedPrefs.getString("ea_login_id", "") ?: "") }
    var loginCode by remember { mutableStateOf(sharedPrefs.getString("login_code", "") ?: "") }

    // Request POST_NOTIFICATIONS permission for Android 13+
    var hasNotificationPermission by remember {
        mutableStateOf(
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                ContextCompat.checkSelfPermission(
                    context,
                    Manifest.permission.POST_NOTIFICATIONS
                ) == PackageManager.PERMISSION_GRANTED
            } else {
                true
            }
        )
    }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        hasNotificationPermission = isGranted
        if (!isGranted) {
            Toast.makeText(context, "Notifications disabled. Enable in Settings for scoreboard alerts.", Toast.LENGTH_LONG).show()
        }
    }

    LaunchedEffect(Unit) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU && !hasNotificationPermission) {
            launcher.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    // Refresh credentials if the JS Bridge updates them under the hood
    val refreshCredentials = {
        serverWanUrl = sharedPrefs.getString("server_wan_url", "") ?: ""
        loginId = sharedPrefs.getString("ea_login_id", "") ?: ""
        loginCode = sharedPrefs.getString("login_code", "") ?: ""
    }

    val bridge = remember { AndroidBridge(context, refreshCredentials) }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B1020)) // Match scoreboard base theme background
    ) {
        // Fullscreen WebView loading assets
        AndroidView(
            modifier = Modifier.fillMaxSize(),
            factory = { ctx ->
                WebView(ctx).apply {
                    webViewClient = WebViewClient()
                    webChromeClient = WebChromeClient()
                    
                    settings.apply {
                        javaScriptEnabled = true
                        domStorageEnabled = true
                        databaseEnabled = true
                        allowFileAccess = true
                        allowContentAccess = true
                        mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                        loadWithOverviewMode = true
                        useWideViewPort = true
                        builtInZoomControls = true
                        displayZoomControls = false
                    }
                    
                    addJavascriptInterface(bridge, "AndroidBridge")
                    loadUrl("file:///android_asset/offline_scoreboard.html")
                }
            }
        )

        // Sleek semi-transparent floating settings button
        FloatingActionButton(
            onClick = { showSettings = true },
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(24.dp)
                .size(48.dp),
            shape = CircleShape,
            containerColor = Color(0x991E2A4A), // Translucent glassmorphism navy blue
            contentColor = Color(0xFFFFD700) // Premium Gold gear icon
        ) {
            Icon(
                imageVector = Icons.Default.Settings,
                contentDescription = "App Settings",
                modifier = Modifier.size(24.dp)
            )
        }

        // Glassmorphic Settings Dialog
        if (showSettings) {
            SettingsDialog(
                currentWanUrl = serverWanUrl,
                currentLoginId = loginId,
                currentLoginCode = loginCode,
                onDismiss = { showSettings = false },
                onSave = { wan, id, code ->
                    sharedPrefs.edit().apply {
                        putString("server_wan_url", wan.trim())
                        putString("ea_login_id", id.trim())
                        putString("login_code", code.trim())
                        apply()
                    }
                    serverWanUrl = wan.trim()
                    loginId = id.trim()
                    loginCode = code.trim()
                    showSettings = false
                    Toast.makeText(context, "Settings saved. Sync targets updated.", Toast.LENGTH_SHORT).show()
                }
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsDialog(
    currentWanUrl: String,
    currentLoginId: String,
    currentLoginCode: String,
    onDismiss: () -> Unit,
    onSave: (String, String, String) -> Unit
) {
    var wanUrl by remember { mutableStateOf(currentWanUrl) }
    var loginId by remember { mutableStateOf(currentLoginId) }
    var loginCode by remember { mutableStateOf(currentLoginCode) }

    Dialog(onDismissRequest = onDismiss) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
                .border(1.dp, Color(0x33FFD700), RoundedCornerShape(16.dp)), // Sleek gold outline border
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(
                containerColor = Color(0xFF0F172E) // Brand dark card background
            )
        ) {
            Column(
                modifier = Modifier
                    .padding(24.dp)
                    .fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Title
                Text(
                    text = "EA SCOREBOARD WAN SYNC",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFFFFD700), // Gold
                    letterSpacing = 1.sp,
                    modifier = Modifier.padding(bottom = 16.dp)
                )

                // Subtitle
                Text(
                    text = "Configure global synchronizer credentials below.",
                    fontSize = 12.sp,
                    color = Color(0xFF8E9CBF),
                    modifier = Modifier.padding(bottom = 20.dp)
                )

                // Server WAN URL Field
                OutlinedTextField(
                    value = wanUrl,
                    onValueChange = { wanUrl = it },
                    label = { Text("Cloudflare Tunnel WAN URL", color = Color(0xFF8E9CBF)) },
                    placeholder = { Text("https://sync.yourdomain.com", color = Color(0x668E9CBF)) },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = Color(0xFFFFD700),
                        unfocusedBorderColor = Color(0x448E9CBF),
                        focusedContainerColor = Color(0xFF080C18),
                        unfocusedContainerColor = Color(0xFF080C18)
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 12.dp)
                )

                // User Login ID Field
                OutlinedTextField(
                    value = loginId,
                    onValueChange = { loginId = it },
                    label = { Text("User Login ID", color = Color(0xFF8E9CBF)) },
                    placeholder = { Text("EA24A01 or Teacher", color = Color(0x668E9CBF)) },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = Color(0xFFFFD700),
                        unfocusedBorderColor = Color(0x448E9CBF),
                        focusedContainerColor = Color(0xFF080C18),
                        unfocusedContainerColor = Color(0xFF080C18)
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 12.dp)
                )

                // User Login Code Field
                OutlinedTextField(
                    value = loginCode,
                    onValueChange = { loginCode = it },
                    label = { Text("Monthly Login Code / Pass", color = Color(0xFF8E9CBF)) },
                    placeholder = { Text("Unique 6-char code", color = Color(0x668E9CBF)) },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = Color.White,
                        unfocusedTextColor = Color.White,
                        focusedBorderColor = Color(0xFFFFD700),
                        unfocusedBorderColor = Color(0x448E9CBF),
                        focusedContainerColor = Color(0xFF080C18),
                        unfocusedContainerColor = Color(0xFF080C18)
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 24.dp)
                )

                // Action Buttons
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    // Cancel Button
                    TextButton(onClick = onDismiss) {
                        Text(text = "CANCEL", color = Color(0xAAFFFFFF))
                    }

                    // Save Button
                    Button(
                        onClick = { onSave(wanUrl, loginId, loginCode) },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Color(0xFFFFD700),
                            contentColor = Color(0xFF0F172E)
                        ),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.padding(start = 8.dp)
                    ) {
                        Text(
                            text = "SAVE CONFIG",
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}
