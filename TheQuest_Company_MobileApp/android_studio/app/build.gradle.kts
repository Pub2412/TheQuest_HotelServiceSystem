plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
}

android {
    namespace = "com.thequest.hotel"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.thequest.hotel"
        minSdk = 23
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }
}

chaquopy {
    defaultConfig {
        version = "3.11"
        pip {
            install("flask==3.0.3")
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
}
