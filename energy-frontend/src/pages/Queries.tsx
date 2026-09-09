import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import PageLayout from "@/components/layout/PageLayout";
import { motion } from "framer-motion";
import { Loader2, Send, Phone, MapPin, Mail } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";

const API_BASE = import.meta.env.VITE_API_URL;

const Queries = () => {
  const [email, setEmail] = useState("");
  const [firstName, setfirstName] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleName = (event) => {
    setfirstName(event.target.value);
  }
  const handlemail = (event) => {
    setEmail(event.target.value);
  }
  const handlemessage = (event) => {
    setMessage(event.target.value);
  }

  const handlEMail = async () => {
    if (!email || !firstName || !message) {
      toast({
        title: "Missing Information",
        description: "Please fill in all fields",
        variant: "destructive",
      });
      return;
    }
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ firstName, email, message }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Something went wrong");
      }
      toast({
        title: "Message Sent",
        description: "Thanks You will hear from us Shortly",
      });

      setfirstName("");
      setEmail("");
      setMessage("");
    }
    catch (error) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive",
      });
    }
    finally {
      setIsLoading(false);
    }
  };

  return (
    <PageLayout>
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-left mb-10"
        >
          <h1 className="text-3xl sm:text-4xl font-bold mb-3">
            <span className="gradient-text">Have a question ? </span>
            Write to us
          </h1>
        </motion.div>

        <div className="transition hover:scale-[1.02]">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-wrap gap-3 mt-12 glass rounded-2xl p-6 shadow-card">

            <Label className="flex justify-left text-2xl">
              First Name
            </Label>
            <Input id="firstname" type="text" value={firstName} onChange={handleName}
              className="p-4 border rounded-lg w-full border text-justify text-lg" placeholder="Enter your first name">
            </Input>
            <Label className="flex justify-left text-2xl">
              Email
            </Label>
            <Input id="Email" type="email" value={email} onChange={handlemail}
              className="p-4 border rounded-lg w-full border text-justify text-lg" placeholder="Enter your Email">
            </Input>
            <Label className="flex justify-left text-2xl">
              Message
            </Label>
            <Textarea id="message" value={message} onChange={handlemessage}
              className="message-input-field p-4 border rounded-lg w-full border h-60 text-justify text-lg" placeholder="Enter your text here">
            </Textarea>
            <Button variant="hero" size="lg" disabled={isLoading} onClick={handlEMail}>
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send />
                  Send Mail
                </>
              )}
            </Button>
          </motion.div>
        </div>
        <div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mt-12 glass rounded-2xl p-8 shadow-card">
            <h2 className="gradient-text text-2xl font-bold mb-3">Contact Us</h2>

            <div className="gap-y-6 sm:grid-cols-2 lg:grid-cols-3">
              <div className="flex items-center gap-4 glass rounded-xl p-5 shadow-card transition hover:scale-[1.02]">
                <div className="flex items-center justify-center w-12 h-12 rounded-full gradient-bg text-white">
                  <MapPin className="w-6 h-6" />
                </div>  
                <p className="p-4 text-lg text-base"> 123-Building, ABC-street, Mumbai, India</p>
              </div>

              <div className="flex items-center gap-4 glass rounded-xl p-5 shadow-card transition hover:scale-[1.02]">
                <div className="flex items-center justify-center w-12 h-12 rounded-full gradient-bg text-white">
                  <Phone className="w-6 h-6" />
                </div>
                <p className="p-4 text-lg text-base"> +91-000 456 0012 </p>
              </div>

              <div className="flex items-center gap-4 glass rounded-xl p-5 shadow-card transition hover:scale-[1.02]">
                <div className="flex items-center justify-center w-12 h-12 rounded-full gradient-bg text-white">
                  <Mail className="w-6 h-6" />
                </div>
                <p className="p-4 text-lg"> support@gmail.com</p>
              </div>
            </div>

          </motion.div>
        </div>
      </div>
    </PageLayout>
  );
};

export default Queries;