#
# Copyright 2018 Picovoice Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from halo import Halo
import time, logging
import argparse
import os
import glob
import struct
import sys
from subprocess import call
from datetime import datetime
from threading import Thread

import deepspeech
from audio_tools import VADAudio
import numpy as np
import pyaudio
import soundfile
from GEBot import GEBot
from Helper.JaroWinklerDistance import JaroWinklerDistance

#sys.path.append(os.path.join(os.path.dirname(__file__), 'binding/python'))
#sys.path.append(os.path.join(os.path.dirname(__file__), 'resources/util/python'))

from pvporcupine import * #Porcupine
#from util import *
import pyttsx3

engine = pyttsx3.init()

engine.setProperty('rate', 150)
engine.setProperty('volume', 0.5)
logging.basicConfig(level=logging.INFO)

class CallPy(object):
        def __init__(self, path = '/home/pi/Desktop/movidius-rpi/faceTracking_Following.py'):
            self.path = path
        
        def call_python_file(self):
            call(["python3", "{}".format(self.path)])
            

class PorcupineDemo(Thread):
    """
    Demo class for wake word detection (aka Porcupine) library. It creates an input audio stream from a microphone,
    monitors it, and upon detecting the specified wake word(s) prints the detection time and index of wake word on
    console. It optionally saves the recorded audio into a file for further review.
    """

    def __init__(
            self,
            library_path,
            model_path,
            keyword_paths,
            sensitivities,
            input_device_index=0,
            output_path=None):

        """
        Constructor.

        :param library_path: Absolute path to Porcupine's dynamic library.
        :param model_file_path: Absolute path to the model parameter file.
        :param keyword_file_paths: List of absolute paths to keyword files.
        :param sensitivities: Sensitivity parameter for each wake word. For more information refer to
        'include/pv_porcupine.h'. It uses the
        same sensitivity value for all keywords.
        :param input_device_index: Optional argument. If provided, audio is recorded from this input device. Otherwise,
        the default audio input device is used.
        :param output_path: If provided recorded audio will be stored in this location at the end of the run.
        """

        super(PorcupineDemo, self).__init__()

        self._library_path = library_path
        self._model_path = model_path
        self._keyword_paths = keyword_paths
        self._sensitivities = sensitivities
        self._input_device_index = input_device_index

        self._output_path = output_path
        if self._output_path is not None:
            self._recorded_frames = []
            
        #Load DeepSpeech model
        print('Initializing model...')
        dirname = os.path.dirname(os.path.abspath(__file__))
        model_name = glob.glob(os.path.join(dirname,'*.pb'))[0]
        logging.info("Model: %s", model_name)
        self.model = deepspeech.Model(model_name)
        try:
            scorer_name = glob.glob(os.path.join(dirname,'*.scorer'))[0]
            logging.info("Language model: %s", scorer_name)
            self.model.enableExternalScorer(scorer_name)
        except Exception as e:
            pass        

    def transcribe(self):
        # Start audio with VAD
        vad_audio = VADAudio(aggressiveness=1,
                             device=None,
                             input_rate=16000,
                             file=None)
        print("Listening (ctrl-C to exit)...")
        frames = vad_audio.vad_collector()

        # Stream from microphone to DeepSpeech using VAD
        spinner = Halo(spinner='line')
        stream_context = self.model.createStream()
        #wav_data = bytearray()
        for frame in frames:
            if frame is not None:
                if spinner: spinner.start()
                logging.debug("streaming frame")
                stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
                #if ARGS.savewav: wav_data.extend(frame)
            else:
                if spinner: spinner.stop()
                logging.debug("end utterence")
                #if ARGS.savewav:
                #    vad_audio.write_wav(os.path.join(ARGS.savewav, datetime.now().strftime("savewav_%Y-%m-%d_%H-%M-%S_%f.wav")), wav_data)
                #    wav_data = bytearray()
                text = stream_context.finishStream()
                print("Recognized: %s" % text)
                if len(text) > 0:
                    # if 'follow me' in text:
                    #     vad_audio.destroy()
                    #     c = CallPy()
                    #     c.call_python_file()
                    #     return 1
                    if 'rotate' in text:
                        step_degree = w2n.word_to_num(text)
                        print(step_degree)
                    else:
                        vad_audio.destroy()
                        question, answer, score = GEBot().ask(text)
                        sys.stdout.buffer.write(answer)
                        engine.say(answer)
                        engine.runAndWait()
                        print("\n")
                stream_context = self.model.createStream()

    def run(self):
        """
         Creates an input audio stream, initializes wake word detection (Porcupine) object, and monitors the audio
         stream for occurrences of the wake word(s). It prints the time of detection for each occurrence and index of
         wake word.
         """

        num_keywords = len(self._keyword_paths)

        keywords = list()
        for x in self._keyword_paths:
            keywords.append(os.path.basename(x).replace('.ppn', '').replace('_compressed', '').split('_')[0])

        print('listening for:')
        for keyword, sensitivity in zip(keywords, self._sensitivities):
            print('- %s (sensitivity: %f)' % (keyword, sensitivity))


        porcupine = None
        pa = None
        audio_stream = None
        try:
            porcupine = Porcupine(
                library_path=self._library_path,
                model_path=self._model_path,
                keyword_paths=self._keyword_paths,
                sensitivities=self._sensitivities)

            pa = pyaudio.PyAudio()
            audio_stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length,
                input_device_index=self._input_device_index)

            while True:
                pcm = audio_stream.read(porcupine.frame_length)

                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

                if self._output_path is not None:
                    self._recorded_frames.append(pcm)

                result = porcupine.process(pcm)

                if result >= 0:
                    engine.say("hi")
                    engine.runAndWait()
                    print('[%s] Detected %s' % (str(datetime.now()), keywords[result]))
                    audio_stream.close()
                    if self.transcribe():
                                    audio_stream = pa.open(
                                    rate=porcupine.sample_rate,
                                    channels=1,
                                    format=pyaudio.paInt16,
                                    input=True,
                                    frames_per_buffer=porcupine.frame_length,
                                    input_device_index=self._input_device_index)

        except KeyboardInterrupt:
            print('stopping ...')
        finally:
            if porcupine is not None:
                porcupine.delete()

            if audio_stream is not None:
                audio_stream.close()

            if pa is not None:
                pa.terminate()

            if self._output_path is not None and len(self._recorded_frames) > 0:
                recorded_audio = np.concatenate(self._recorded_frames, axis=0).astype(np.int16)
                soundfile.write(self._output_path, recorded_audio, samplerate=porcupine.sample_rate, subtype='PCM_16')

    _AUDIO_DEVICE_INFO_KEYS = ['index', 'name', 'defaultSampleRate', 'maxInputChannels']

    @classmethod
    def show_audio_devices_info(cls):
        """ Provides information regarding different audio devices available. """

        pa = pyaudio.PyAudio()

        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            print(', '.join("'%s': '%s'" % (k, str(info[k])) for k in cls._AUDIO_DEVICE_INFO_KEYS))

        pa.terminate()

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--keywords', help='comma-separated list of default keywords (%s)' % ', '.join(sorted(KEYWORDS)))

    parser.add_argument('--keyword_paths', help='comma-separated absolute paths to keyword files')

    parser.add_argument('--library_path', help="absolute path to Porcupine's dynamic library", default=LIBRARY_PATH)

    parser.add_argument('--model_path', help='absolute path to model parameter file', default=MODEL_PATH)

    parser.add_argument('--sensitivities', help='detection sensitivity [0, 1]', default=0.5)

    parser.add_argument('--input_audio_device_index', help='index of input audio device', type=int, default=None)

    parser.add_argument(
        '--output_path',
        help='absolute path to where recorded audio will be stored. If not set, it will be bypassed.')

    parser.add_argument('--show_audio_devices_info', action='store_true')

    args = parser.parse_args()

    if args.show_audio_devices_info:
        PorcupineDemo.show_audio_devices_info()
    else:
        if args.keyword_paths is None:
            if args.keywords is None:
                raise ValueError('either --keywords or --keyword_file_paths must be set')

            keywords = [x.strip() for x in args.keywords.split(',')]

            if all(x in KEYWORDS for x in keywords):
                keyword_paths = [KEYWORD_PATHS[x] for x in keywords]
            else:
                raise ValueError(
                    'selected keywords are not available by default. available keywords are: %s' % ', '.join(KEYWORDS))
        else:
            keyword_paths = [x.strip() for x in args.keyword_paths.split(',')]

        if isinstance(args.sensitivities, float):
            sensitivities = [args.sensitivities] * len(keyword_paths)
        else:
            sensitivities = [float(x) for x in args.sensitivities.split(',')]

        PorcupineDemo(
            library_path=args.library_path,
            model_path=args.model_path,
            keyword_paths=keyword_paths,
            sensitivities=sensitivities,
            output_path=args.output_path,
            input_device_index=args.input_audio_device_index).run()


if __name__ == '__main__':
    main()
