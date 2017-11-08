from Sompyler.score.stressor import Stressor
from Sompyler.score.chord import Chord

def stress_range(stress):
    if isinstance(stress, int):
        return (stress, 1)
    elif not isinstance(stress, tuple):
        if isinstance(stress, str):
            stress = [ int(x) for x in stress.split("-", 1) ]
        return (
            stress[0],
            stress[1] * 1.0 / stress[0]
        )



class Measure(object):
    __slots__ = (
        'seconds_per_tick', 'stressor', 'offset', 'length', 'structure',
        'voices', 'measure_cut', 'lower_stress_bound', 'upper_stress_bound'
    )

    def __init__(
            self, structure, stage, previous, measure_cut=None,
            stress_pattern=None, ticks_per_minute=None,
            lower_stress_bound=None, upper_stress_bound=None
        ):

        self.measure_cut = measure_cut or 0

        if previous:
            self.offset = (
                previous.offset + previous.calculate_seconds_from_ticks(
                    previous.length
                )
            )
        else:
            self.offset = 0
            if ticks_per_minute is None:
                raise RuntimeError(
                    "First measure must have a tempo (meta[ticks_per_minute])"
                )

        if stress_pattern is not None:
            self.stressor = Stressor( stress_pattern.split(";") )
        else:
            self.stressor = previous.stressor

        if ticks_per_minute is None:
            self.seconds_per_tick = previous.seconds_per_tick
        elif isinstance(ticks_per_minute, int):
            self.seconds_per_tick = (60.0 / ticks_per_minute, 1)
        elif not isinstance(ticks_per_minute, tuple):

            if isinstance(ticks_per_minute, str):
                tickets_per_minute = [
                    int(x) for x in ticks_per_minute.split("-", 1)
                ]
                tickets_per_minute.append( tickets_per_minute[0] )

            self.seconds_per_tick = (
                60.0 / ticks_per_minute[0],
                ticks_per_minute[0] * 1.0 / ticks_per_minute[1]
            )

        self.lower_stress_bound = (
            stress_range(lower_stress_bound)
                if lower_stress_bound
                else previous.lower_stress_bound
        )

        self.upper_stress_bound = (
            stress_range(upper_stress_bound)
                if upper_stress_bound
                else previous.upper_stress_bound
        )

        self.structure = structure
        self.voices = stage.voices

        self.length = self.stressor.cumlen - (
            abs(self.measure_cut)
                if self.measure_cut < 0
                else 0
        )

    def calculate_seconds_from_ticks( self, offset, length=None ):

        if offset > self.length:
            raise ValueError("Offset exceeding " + max_offset)

        if offset < self.measure_cut > 0:
            raise ValueError(
                "Offset too low, must be at least"
                + self.measure_cut
            )

        exp_div = 1.0 / self.stressor.cumlen

        spt, spt_factor = self.seconds_per_tick

        def seconds(ticks):
            ticks += offset
            return spt * ( ticks if spt_factor == 1 else (
                           ( spt_factor ** (ticks*exp_div) - 1 )
                         / ( spt_factor **        exp_div  - 1 )
                       )
                   )

        offset_s = seconds(0)

        if length:
            return offset_s, seconds(length) - offset_s
        else:
            return offset_s


    def stress_of_tick( self, tick ):

        offset = 1.0 * tick / self.stressor.cumlen

        ls, ls_factor = self.lower_stress_bound
        ls = ls * ls_factor**offset

        us, us_factor = self.upper_stress_bound
        us = us * us_factor**offset

        stress = ls * (us/ls) ** self.stressor.of( round(offset) )
        
        return stress

    def __iter__(self):

        for v_name, v_chords in self.structure.items():
            # merge general and voice-specific _meta, if any
            v_meta = v_chords.pop('_meta', {})
            if 'stressor' in v_meta:
                v_meta['stressor'] = Stressor( v_meta['stressor'].split(";") )
                if not v_meta['stressor'].cumlen == self.stressor.cumlen:
                    raise RuntimeError(
                        "Voice bound measure stressor has other length "
                        "than global measure"
                    )

            for prop in 'stressor', 'lower_stress_bound', 'upper_stress_bound':
                if prop not in v_meta:
                    v_meta[prop] = getattr(self, prop)

            yield VoiceBoundMeasure(
                 self, self.voices[v_name], v_chords, **v_meta
            )


class VoiceBoundMeasure(Measure):
    __slots__ = ('measure', 'voice', 'chords')

    def __init__(
            self, measure, voice, ch_data,
            stressor=None,
            lower_stress_bound=None,
            upper_stress_bound=None
        ):

        self.measure  = measure
        self.voice    = voice
        self.stressor = stressor or measure.stressor

        self.lower_stress_bound = (
            stress_range(lower_stress_bound)
                if lower_stress_bound
                else measure.lower_stress_bound
        )

        self.upper_stress_bound = (
            stress_range(upper_stress_bound)
                if upper_stress_bound
                else measure.upper_stress_bound
        )

        self.chords   = ch_data

    def __iter__(self):

        calc_span = self.measure.calculate_seconds_from_ticks

        all_offsets = set( self.chords.values() )

        for offset, chord in self.chords.items():

            if not isinstance(chord, list):
                note = chord
                chord = [note]

            yield Chord(
                self.measure.offset, offset, self.voice,
                self.stressor.of(offset, all_offsets),
                calc_span, chord
            )
