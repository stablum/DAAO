package com.tiagocalvados.daao

import kotlin.math.atan2
import kotlin.math.hypot

data class CameraPose(
    val magneticBearingDegrees: Double?,
    val elevationDegrees: Double,
    val deviceTopBearingDegrees: Double?,
)

object OrientationMath {
    /**
     * Converts Android's device-to-world rotation matrix into the direction of
     * the rear camera. World axes are East, magnetic North, Up. Device -Z is
     * the rear camera's viewing direction and device +Y points to its top edge.
     */
    fun cameraPose(rotationMatrix: FloatArray): CameraPose {
        require(rotationMatrix.size >= 9) { "A 3x3 rotation matrix is required" }

        val cameraEast = -rotationMatrix[2].toDouble()
        val cameraNorth = -rotationMatrix[5].toDouble()
        val cameraUp = -rotationMatrix[8].toDouble()
        val cameraHorizontal = hypot(cameraEast, cameraNorth)

        val topEast = rotationMatrix[1].toDouble()
        val topNorth = rotationMatrix[4].toDouble()
        val topHorizontal = hypot(topEast, topNorth)

        return CameraPose(
            magneticBearingDegrees = heading(cameraEast, cameraNorth, cameraHorizontal),
            elevationDegrees = Math.toDegrees(atan2(cameraUp, cameraHorizontal)),
            deviceTopBearingDegrees = heading(topEast, topNorth, topHorizontal),
        )
    }

    private fun heading(east: Double, north: Double, horizontal: Double): Double? {
        if (horizontal < 1e-6) {
            return null
        }
        val degrees = Math.toDegrees(atan2(east, north))
        return (degrees + 360.0) % 360.0
    }
}
