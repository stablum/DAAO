package com.tiagocalvados.daao

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import java.util.concurrent.atomic.AtomicReference

data class OrientationSnapshot(
    val sensorTimestampNs: Long,
    val cameraPose: CameraPose,
    val pitchDegrees: Double,
    val rollDegrees: Double,
    val quaternionW: Double,
    val quaternionX: Double,
    val quaternionY: Double,
    val quaternionZ: Double,
    val headingAccuracyDegrees: Double?,
    val sensorAccuracy: Int,
)

class OrientationTracker(context: Context) : SensorEventListener {
    private val sensorManager =
        context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val rotationSensor =
        sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)
            ?: sensorManager.getDefaultSensor(Sensor.TYPE_GEOMAGNETIC_ROTATION_VECTOR)
    private val latest = AtomicReference<OrientationSnapshot?>()

    val isAvailable: Boolean
        get() = rotationSensor != null

    val sensorName: String?
        get() = rotationSensor?.name

    fun start() {
        rotationSensor?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
        }
    }

    fun stop() {
        sensorManager.unregisterListener(this)
    }

    fun snapshot(): OrientationSnapshot? = latest.get()

    override fun onSensorChanged(event: SensorEvent) {
        if (event.sensor.type != Sensor.TYPE_ROTATION_VECTOR &&
            event.sensor.type != Sensor.TYPE_GEOMAGNETIC_ROTATION_VECTOR
        ) {
            return
        }

        val matrix = FloatArray(9)
        SensorManager.getRotationMatrixFromVector(matrix, event.values)
        val orientation = FloatArray(3)
        SensorManager.getOrientation(matrix, orientation)
        val quaternion = FloatArray(4)
        SensorManager.getQuaternionFromVector(quaternion, event.values)
        val headingAccuracy =
            event.values.getOrNull(4)
                ?.takeIf { it.isFinite() && it >= 0f }
                ?.let { Math.toDegrees(it.toDouble()) }

        latest.set(
            OrientationSnapshot(
                sensorTimestampNs = event.timestamp,
                cameraPose = OrientationMath.cameraPose(matrix),
                pitchDegrees = Math.toDegrees(orientation[1].toDouble()),
                rollDegrees = Math.toDegrees(orientation[2].toDouble()),
                quaternionW = quaternion[0].toDouble(),
                quaternionX = quaternion[1].toDouble(),
                quaternionY = quaternion[2].toDouble(),
                quaternionZ = quaternion[3].toDouble(),
                headingAccuracyDegrees = headingAccuracy,
                sensorAccuracy = event.accuracy,
            ),
        )
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit
}
