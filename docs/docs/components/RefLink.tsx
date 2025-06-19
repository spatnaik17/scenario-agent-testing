export const RefLink = ({
  link,
  children,
}: {
  link: string;
  children: React.ReactNode;
}) => {
  return (
    <a
      href={`/reference/python/scenario/${link}`}
      target="reference"
      style={{
        color: "var(--vocs-color_textAccent)",
      }}
    >
      {children}
    </a>
  );
};
