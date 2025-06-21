import { Link as RouterLink } from "react-router";

export const Link = ({
  href,
  children,
  className,
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
}) => {
  return (
    <RouterLink to={href} className={className}>
      {children}
    </RouterLink>
  );
};
