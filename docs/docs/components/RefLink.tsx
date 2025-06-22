export const RefLink = ({
  link,
  code,
  children,
}: {
  link: { python: string; typescript?: string };
  code?: { python: string; typescript?: string };
  children?: React.ReactNode;
}) => {
  return (
    <a
      href={`/reference/python/scenario/${link.python}`}
      target="reference"
      className="underline decoration-dotted decoration-gray-400 hover:no-underline"
    >
      {children ? children : <code className="vocs_Code">{code?.python}</code>}
    </a>
  );
};
