package com.example.eascoreboard

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.HttpURLConnection
import java.net.URL
import org.json.JSONObject

class SyncNotificationWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        val sharedPref = applicationContext.getSharedPreferences("EASecurePrefs", Context.MODE_PRIVATE)
        val wanUrl = sharedPref.getString("server_wan_url", "") ?: ""
        val loginId = sharedPref.getString("ea_login_id", "") ?: ""
        val loginCode = sharedPref.getString("login_code", "") ?: ""

        if (wanUrl.isEmpty() || loginId.isEmpty() || loginCode.isEmpty()) {
            return Result.success() // Not configured yet, skip silently
        }

        try {
            // Trim URL and resolve check-updates endpoint
            val cleanUrl = wanUrl.trim().removeSuffix("/")
            val checkUrl = "$cleanUrl/scoreboard/auth/check-updates"
            
            val url = URL(checkUrl)
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.connectTimeout = 10000
            conn.readTimeout = 10000
            
            // Set headers for credentials
            conn.setRequestProperty("X-EA-Login-ID", loginId)
            conn.setRequestProperty("X-EA-Login-Code", loginCode)
            conn.setRequestProperty("Accept", "application/json")
            
            val responseCode = conn.responseCode
            if (responseCode == 200) {
                val reader = BufferedReader(InputStreamReader(conn.inputStream))
                val response = StringBuilder()
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    response.append(line)
                }
                reader.close()

                val json = JSONObject(response.toString())
                val success = json.optBoolean("success", false)
                if (success) {
                    val serverUpdatedAt = json.optString("server_updated_at", "")
                    val latestActivity = json.optString("latest_activity", "No recent activity")
                    
                    // Check if we have seen this update before
                    val lastSeenUpdate = sharedPref.getString("last_seen_update_timestamp", "")
                    if (serverUpdatedAt.isNotEmpty() && serverUpdatedAt != lastSeenUpdate) {
                        // We have a new update! Save it and fire a notification!
                        sharedPref.edit().putString("last_seen_update_timestamp", serverUpdatedAt).apply()
                        
                        showNotification(
                            "Scoreboard Updated!",
                            latestActivity
                        )
                    }
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
            // In background polling, fail silently and retry next time
        }

        return Result.success()
    }

    private fun showNotification(title: String, message: String) {
        val notificationManager = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channelId = "ea_scoreboard_updates"

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Scoreboard Updates",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "Notifies teachers and students of score changes and announcements."
            }
            notificationManager.createNotificationChannel(channel)
        }

        val notification = NotificationCompat.Builder(applicationContext, channelId)
            .setSmallIcon(android.R.drawable.ic_dialog_info) // Standard system info icon
            .setContentTitle(title)
            .setContentText(message)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        notificationManager.notify(System.currentTimeMillis().toInt(), notification)
    }
}
