/* vim: set ts=4 sw=4 et: */

package org.gitorious.scrapfilbleu.android;

import java.util.Random;
import android.graphics.Color;

public class ColorGenerator {
	Random rand;

	public ColorGenerator() {
		this.rand = new Random();
	}

	public int pick() {
		return Color.argb(
			255,
			this.rand.nextInt(256),
			this.rand.nextInt(256),
			this.rand.nextInt(256)
		);
	}
}
