package com.tiagocalvados.daao

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class OrientationMathTest {
    @Test
    fun rearCameraFacingNorthIsZeroDegrees() {
        val pose = OrientationMath.cameraPose(
            floatArrayOf(
                1f, 0f, 0f,
                0f, 0f, -1f,
                0f, 1f, 0f,
            ),
        )

        assertEquals(0.0, pose.magneticBearingDegrees!!, 0.0001)
        assertEquals(0.0, pose.elevationDegrees, 0.0001)
    }

    @Test
    fun rearCameraFacingEastIsNinetyDegrees() {
        val pose = OrientationMath.cameraPose(
            floatArrayOf(
                0f, 0f, -1f,
                -1f, 0f, 0f,
                0f, 1f, 0f,
            ),
        )

        assertEquals(90.0, pose.magneticBearingDegrees!!, 0.0001)
        assertEquals(0.0, pose.elevationDegrees, 0.0001)
    }

    @Test
    fun rearCameraPointingDownHasNoDefinedBearing() {
        val pose = OrientationMath.cameraPose(
            floatArrayOf(
                1f, 0f, 0f,
                0f, 1f, 0f,
                0f, 0f, 1f,
            ),
        )

        assertNull(pose.magneticBearingDegrees)
        assertEquals(-90.0, pose.elevationDegrees, 0.0001)
        assertEquals(0.0, pose.deviceTopBearingDegrees!!, 0.0001)
    }
}
