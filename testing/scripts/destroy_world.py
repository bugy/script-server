#!/usr/bin/python3
import time

text = """
Stars are born, they live, and they die. The sun is no different, and when it goes, the Earth goes with it. But our planet won't go quietly into the night.

Rather, when the sun expands into a red giant during the throes of death, it will vaporize the Earth.

Perhaps not the story you were hoping for, but there's no need to start buying star-death insurance yet. The time scale is long — 7 billion or 8 billion years from now, at least. Humans have been around only about 40-thousandth that amount of time; if the age of the Earth were compressed into a 24-hour day, humans would occupy only the last second, at most. If contemplating stellar lifetimes does nothing else, it should underscore the existential insignificance of our lives. [What If Earth Were Twice as Big?]

So what happens when the sun goes out? The answer has to do with how the sun shines. Stars begin their lives as big agglomerations of gas, mostly hydrogen with a dash of helium and other elements. Gas has mass, so if you put a lot of it in one place, it collapses in on itself under its own weight. That creates pressure on the interior of the proto-star, which heats up the gas until it gets so hot that the electrons get stripped off the atoms and the gas becomes charged, or ionized (a state called a plasma). The hydrogen atoms, each containing a single proton, fuse with other hydrogen atoms to become helium, which has two protons and two neutrons. The fusion releases energy in the form of light and heat, which creates outward pressure, and stops the gas from collapsing any further. A star is born (with apologies to Barbra Streisand).

There's enough hydrogen to keep this process going for billions of years. But eventually, almost all of the hydrogen in the sun's core will have fused into helium. At that point, the sun won't be able to generate as much energy, and will start to collapse under its own weight. That weight can't generate enough pressure to fuse the helium as it did with the hydrogen at the beginning of the star's life. But what hydrogen is left on the core's surface wil fuse, generating a little additional energy and allowing the sun to keep shining.

That helium core, though, will start to collapse in on itself. When it does, it releases energy, though not through fusion. Instead it just heats up because of increased pressure (compressing any gas increases its temperature). That release of energy results in more light and heat, making the sun even brighter. On a darker note, however, the energy also causes the sun to bloat into a red giant. Red giants are red because their surface temperatures are lower than stars like the sun. Even so, they are much bigger than their hotter counterparts.

A 2008 study by astronomers Klaus-Peter Schröder and Robert Connon Smith estimated that the sun will get so large that its outermost surface layers will reach about 108 million miles (about 170 million kilometers) out, absorbing the planets Mercury, Venus and Earth. The whole process of turning into a red giant will take about 5 million years, a relative blip in the sun's lifetime. [50 Interesting Facts About Earth]

On the bright side, the sun's luminosity is increasing by a factor of about 10 percent every billion years. The habitable zone, where liquid water can exist on a planet's surface, right now is between about 0.95 and 1.37 times the radius of the Earth's orbit (otherwise known as astronomical units, or AU). That zone will continue to move outward. By the time the sun gets ready to become a red giant, Mars will have been inside the zone for quite some time. Meanwhile, Earth will be baking and turning into a steam bath of a planet, with its oceans evaporating and breaking down into hydrogen and oxygen.

As the water gets broken down, the hydrogen will escape to space and the oxygen will react with surface rocks. Nitrogen and carbon dioxide will probably become the major components of the atmosphere — rather like Venus is today, though it's far from clear whether the Earth's atmosphere will ever get so thick. Some of that answer depends on how much volcanism is still going on and how fast plate tectonics winds down. Our descendants will, one hopes, have opted to go to Mars by then — or even farther out in the solar system. [What If Every Volcano on Earth Erupted at Once?]

But even Mars won't last as a habitable planet. Once the sun becomes a giant, the habitable zone will move out to between 49 and 70 astronomical units. Neptune in its current orbit would probably become too hot for life; the place to live would be Pluto and the other dwarf planets, comets and ice-rich asteroids in the Kuiper Belt.

One effect Schröder and Smith note is that stars like the sun lose mass over time, primarily via the solar wind. Planets' orbits around the sun will slowly expand. It won't happen fast enough to save the Earth, but if Neptune edges far enough out it could become a home for humans, with some terraforming.

Eventually, though, the hydrogen in the sun's outer core will get depleted, and the sun will start to collapse once again, triggering another cycle of fusion. For about 2 billion years the sun will fuse helium into carbon and some oxygen, but there's less energy in those reactions. Once the last bits of helium turn into heavier elements, there's no more radiant energy to keep the sun puffed up against it's own weight. The core will shrink into a white dwarf. The distended sun's outer layers are only weakly bound to the core because they are so far away from it, so when the core collapses it will leave the outer layers of its atmosphere behind. The result is a planetary nebula.

Since white dwarfs are heated by compression rather than fusion, initially they are quite hot — surface temperatures can reach 50,000 degrees Fahrenheit (nearly 28,000 degrees Celsius) — and they illuminate the slowly expanding gas in the nebula. So any alien astronomers billions of years in the future might see something like the Ring Nebula in Lyra where the sun once shone. 
"""

sections = text.split("\n\n")

for i, section in enumerate(sections):
    words = section.split(" ")
    line = ""
    for word in words:
        line_length = len(line)
        if line.rfind("\n") > 0:
            line_length -= line.rfind("\n")

        if line_length > 100:
            print(line)
            line = ""
            time.sleep(0.3)

        if line:
            line += " "
        line += word

    if line:
        print(line)

    if i < (len(sections) - 1):
        print()

        correct_answer = None
        print("Want to continue? Y/N")
        while correct_answer is None:
            answer = input()
            if not (answer in ["Y", "N"]):
                print("put correct answer")
            else:
                correct_answer = answer

        if correct_answer == "Y":
            # just continuing
            pass
        elif correct_answer == "N":
            print("Bye bye!")
            break
