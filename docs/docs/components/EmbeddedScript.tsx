import { useEffect, useRef } from "react";

export const EmbeddedScript = ({ id, src }: { id: string; src: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const script = document.createElement("script");
    script.src = src;
    script.id = id;
    script.async = true;

    if (containerRef.current) {
      containerRef.current.appendChild(script);
    }

    return () => {
      if (containerRef.current?.contains(script)) {
        containerRef.current.removeChild(script);
      }
    };
  }, [id, src]);

  return <div ref={containerRef} />;
};
