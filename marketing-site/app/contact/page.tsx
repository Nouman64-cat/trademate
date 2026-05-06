// app/contact/page.tsx
import type { Metadata } from "next";
import ContactForm from "@/components/contact/ContactForm";

export const metadata: Metadata = {
  title: "Contact",
  description:
    `Request a live demo of ${process.env.NEXT_PUBLIC_APP_NAME} or get in touch with the team. We'll walk you through a real trade query end-to-end.`,
};

export default function ContactPage() {
  return <ContactForm />;
}
