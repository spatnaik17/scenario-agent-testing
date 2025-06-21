import { cn } from "./utils";

export function HStack({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={cn("flex flex-row", className ?? "")}>{children}</div>;
}
