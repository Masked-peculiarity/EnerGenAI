import { useEffect, useRef, useState } from "react";

export const useSpeechToText = () => {
  const recognitionRef = useRef<any>(null);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn("Speech Recognition not supported");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript;
      setTranscript(text);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onerror = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
  }, []);

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setTranscript("");
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    recognitionRef.current?.stop();
    setIsListening(false);
  };

  return {
    transcript,
    isListening,
    startListening,
    stopListening,
  };
};
