export const RefLink = ({
  link,
  code,
}: {
  link: { python: string; typescript?: string };
  code: { python: string; typescript?: string };
}) => {
  return (
    <a
      href={`/reference/python/scenario/${link.python}`}
      target="reference"
      className="underline decoration-dotted decoration-gray-400 hover:no-underline"
    >
      <code className="vocs_Code">{code.python}</code>
    </a>
  );
};
