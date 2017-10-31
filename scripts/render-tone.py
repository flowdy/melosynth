import sys, argparse, script_preamble
from Sompyler.synthesizer import SAMPLING_RATE, BYTES_PER_CHANNEL

parser = argparse.ArgumentParser(description="Render a single tone")
parser.add_argument("instrument", type=str, nargs='?',
    metavar="instrument",
    help="Sompyler instrument definition file, YAML or JSON format. Pitch indication (-f num) is required.")
parser.add_argument("-O", "--oscillator",
    choices=("sine","square","sawtooth","noise","what"),
    help="Form of oscillation")
parser.add_argument("--frequency", "--pitch", "-f", type=float, dest='pitch',
    help="Number of oscillations per second" )
parser.add_argument("-l", "--length", type=float,
    required=True,
    help="Duration of tone in seconds" )
parser.add_argument("-s", "--stress", type=float, default=1,
    help="Intensity of tone")
parser.add_argument("-A", "--attack", metavar="SHAPE", dest='A',
    help="Attack shape")
parser.add_argument("-S", "--sustain", metavar="SHAPE", dest='S',
    help="Sustain shape (if attack is not given, simply shape)")
parser.add_argument("-T", "--tail", metavar="SHAPE", dest='T',
    help="Tail shape, to regain minimal amplitude when transitioning from sustain to release")
parser.add_argument("-R", "--release", metavar="SHAPE", dest='R',
    help="Release shape, not included in the length specified.")
parser.add_argument("-AM", "--amplitude-modulation", metavar="MOD_DEF", dest="AM")
parser.add_argument("-FM", "--frequency-modulation", metavar="MOD_DEF", dest="FM")
parser.add_argument("-WS", "--wave-shape", metavar="SHAPE", dest="WS",
    help="Form of each oscillation, projected")
parser.add_argument("--sound", action='store_true',
    help="If you want sound, make sure you specify an instrument or an oscillator, and a pitch, too." )
parser.add_argument("--output", "-o", metavar="FILE",
    help="If you want sound, specify a filename with .wav, .flac, or .mp3 "
         "extension to choose the respective file type (default is .wav). "
         "Otherwise, you might want to choose .png just to remind yourself "
         "that it is a PNG image.")
args = parser.parse_args()

class ArgumentError(Exception):
    pass

if bool(args.pitch) ^ (bool(args.oscillator) ^ bool(args.instrument)):
    raise ArgumentError(
        "If pitch is given, either oscillator or an "
        "instrument definition file must also be specified, and vice versa. "
        "Show help with --help option."
    )
elif args.oscillator and args.instrument:
    raise ArgumentError(
        "Oscillator and instrument definition filename conflict when being "
        "both are specified. Show help with --help option."
    )

if not args.pitch and (args.sound or args.FM or args.WS):
    raise ArgumentError(
        "For sound output (or to apply frequency modulation or waveshaping), "
        "a pitch and either an oscillator or an instrument definition "
        "filename must be specified."
    )

properties = {}
for i in ('A', 'S', 'T', 'R', 'FM', 'AM', 'WS'):
    arg = getattr(args, i)
    if arg is None:
        continue
    properties[i] = arg

def display_graph(curve):
    import matplotlib.pyplot as plt
    if isinstance(curve, dict):
        raise NotImplemented
    else:
        plt.plot(range(len(curve)), curve)
        plt.show()

def generate_sound_file(tone, filename):
    import soundfile
    from tempfile import NamedTemporaryFile
    format = {}
    if filename is None:
        file = NamedTemporaryFile(suffix=".wav", delete=False)
        filename = file.name
        format["format"] = "WAV"
        format["subtype"] = "PCM_" + str(8 * BYTES_PER_CHANNEL)
    else:
        file = filename
    soundfile.write(file, tone, SAMPLING_RATE, **format)
    print "Successfully written sound file {}!".format(filename)

if args.instrument:
    # render tone of the specified instrument
    if properties:
        raise Exception(
            "Cannot overwrite instrument definition with "
          + properties.keys().join(", ") + "."
        )
    from Sompyler.orchestra.instrument import Instrument
    instr = Instrument(args.instrument)
    tone = instr.render_tone(
        args.pitch, args.length,
        args.stress
    )
    if args.sound:
        generate_sound_file(tone, args.output)
    display_graph(tone)

elif args.oscillator:
    print "Render tone of a sympartial ..."
    from Sompyler.orchestra.instrument.protopartial import ProtoPartial
    from Sompyler.synthesizer.oscillator import CORE_PRIMITIVE_OSCILLATORS
    properties['O'] = CORE_PRIMITIVE_OSCILLATORS()[ args.oscillator ]
    sympartial = ProtoPartial(None, None, None, **properties).sympartial()
    tone = sympartial.render(
        args.pitch, args.stress, args.length, {}
    )
    if args.sound:
        generate_sound_file(tone, args.output)
    display_graph(tone)

elif args.A:
    print "Rendering bare envelope ..."
    from Sompyler.synthesizer.envelope import Envelope
    env = Envelope(args.A, args.S, args.T, args.R)
    display_graph(env.render(args.length))

elif args.S:
    print "Rendering bare shape ..."
    from Sompyler.synthesizer.shape import Shape
    display_graph(
        Shape.from_string(properties['S']).render(args.length * SAMPLING_RATE)
    )

else:
    raise sys.exit("No clue what to render")

